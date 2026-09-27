from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.notifications.models import ConsentStatus, Notification, NotificationChannel, NotificationConsent, NotificationStatus
from app.modules.notifications.schemas import ConsentCreate, ConsentRead, NotificationCreate, NotificationRead, NotificationResult, PHONE_RE
from app.modules.patients.models import Patient
from app.modules.scheduling.models import Appointment
from app.platform.database import get_session
from app.platform.attachments import attachment_response, read_signed_attachment, store_attachment
from app.platform.errors import ConflictError, NotFoundError
from app.platform.types import utc_now

router = APIRouter(prefix="/patients/{patient_id}", tags=["notifications"])
Db = Annotated[AsyncSession, Depends(get_session)]
Staff = Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))]
InternalAdmin = Annotated[CurrentUser, Depends(require_roles("admin"))]


async def patient_or_404(session: AsyncSession, patient_id: UUID, *, lock: bool = False) -> Patient:
    statement = select(Patient).where(Patient.id == patient_id)
    if lock:
        statement = statement.with_for_update()
    patient = await session.scalar(statement)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")
    return patient


async def notification_or_404(session: AsyncSession, patient_id: UUID, notification_id: UUID, *, lock: bool = False) -> Notification:
    statement = select(Notification).where(Notification.id == notification_id, Notification.patient_id == patient_id)
    if lock:
        statement = statement.with_for_update()
    notification = await session.scalar(statement)
    if notification is None:
        raise NotFoundError("Notification not found")
    return notification


@router.get("/notification-consents", response_model=list[ConsentRead])
async def list_consents(patient_id: UUID, user: Staff, session: Db) -> list[NotificationConsent]:
    await patient_or_404(session, patient_id)
    consents = list((await session.scalars(select(NotificationConsent).where(NotificationConsent.patient_id == patient_id).order_by(NotificationConsent.created_at.desc(), NotificationConsent.id.desc()))).all())
    record_event(session, actor_id=str(user.id), action="notification_consents.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return consents


@router.post("/notification-consents", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
async def grant_consent(patient_id: UUID, payload: ConsentCreate, user: Staff, session: Db) -> NotificationConsent:
    await patient_or_404(session, patient_id, lock=True)
    previous = await latest_consent(session, patient_id, payload.channel)
    if previous is not None and previous.status == ConsentStatus.GRANTED:
        raise ConflictError("Revoke the current authorization before recording a new signed version")
    consent = NotificationConsent(patient_id=patient_id, channel=payload.channel, granted_at=payload.granted_at, evidence_location=payload.evidence_location, recorded_by=user.id)
    session.add(consent)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="notification_consent.granted", resource_type="notification_consent", resource_id=consent.id)
    await session.commit()
    await session.refresh(consent)
    return consent


async def latest_consent(session: AsyncSession, patient_id: UUID, channel: NotificationChannel) -> NotificationConsent | None:
    return await session.scalar(
        select(NotificationConsent)
        .where(NotificationConsent.patient_id == patient_id, NotificationConsent.channel == channel)
        .order_by(NotificationConsent.created_at.desc(), NotificationConsent.id.desc())
        .limit(1)
    )


@router.post("/notification-consents/with-attachment", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
async def grant_consent_with_attachment(
    patient_id: UUID,
    metadata: Annotated[str, Form()],
    attachment: Annotated[UploadFile, File()],
    user: Staff,
    session: Db,
) -> NotificationConsent:
    await patient_or_404(session, patient_id, lock=True)
    try:
        payload = ConsentCreate.model_validate_json(metadata)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid notification authorization metadata") from exc
    previous = await latest_consent(session, patient_id, payload.channel)
    if previous is not None and previous.status == ConsentStatus.GRANTED:
        raise ConflictError("Revoke the current authorization before recording a new signed version")
    document = await read_signed_attachment(attachment)
    consent = NotificationConsent(patient_id=patient_id, channel=payload.channel, granted_at=payload.granted_at, evidence_location=payload.evidence_location, recorded_by=user.id)
    store_attachment(consent, document)
    session.add(consent)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="notification_consent.granted_with_attachment", resource_type="notification_consent", resource_id=consent.id)
    await session.commit()
    await session.refresh(consent)
    return consent


@router.put("/notification-consents/{consent_id}/attachment", response_model=ConsentRead)
async def attach_notification_consent_document(
    patient_id: UUID,
    consent_id: UUID,
    attachment: Annotated[UploadFile, File()],
    user: Staff,
    session: Db,
) -> NotificationConsent:
    await patient_or_404(session, patient_id)
    consent = await session.scalar(
        select(NotificationConsent).where(NotificationConsent.id == consent_id, NotificationConsent.patient_id == patient_id).with_for_update()
    )
    if consent is None:
        raise NotFoundError("Notification consent not found")
    if consent.attachment_filename is not None:
        raise ConflictError("A signed document is already attached to this authorization")
    store_attachment(consent, await read_signed_attachment(attachment))
    record_event(session, actor_id=str(user.id), action="notification_consent.attachment_added", resource_type="notification_consent", resource_id=consent.id)
    await session.commit()
    await session.refresh(consent)
    return consent


@router.get("/notification-consents/{consent_id}/attachment")
async def download_notification_consent_document(patient_id: UUID, consent_id: UUID, user: Staff, session: Db) -> Response:
    await patient_or_404(session, patient_id)
    consent = await session.scalar(
        select(NotificationConsent)
        .options(undefer(NotificationConsent.attachment_data))
        .where(NotificationConsent.id == consent_id, NotificationConsent.patient_id == patient_id)
    )
    if consent is None:
        raise NotFoundError("Notification consent not found")
    response = attachment_response(consent)
    record_event(session, actor_id=str(user.id), action="notification_consent.attachment_downloaded", resource_type="notification_consent", resource_id=consent.id)
    await session.commit()
    return response


@router.post("/notification-consents/{channel}/revoke", response_model=ConsentRead)
async def revoke_consent(patient_id: UUID, channel: NotificationChannel, user: Staff, session: Db) -> NotificationConsent:
    await patient_or_404(session, patient_id, lock=True)
    consent = await latest_consent(session, patient_id, channel)
    if consent is None:
        raise NotFoundError("Notification consent not found")
    if consent.status == ConsentStatus.REVOKED:
        raise ConflictError("Notification consent is already revoked")
    consent.status = ConsentStatus.REVOKED
    consent.revoked_at = utc_now()
    pending = list(
        (
            await session.scalars(
                select(Notification).where(
                    Notification.patient_id == patient_id,
                    Notification.channel == channel,
                    Notification.status == NotificationStatus.PENDING,
                )
            )
        ).all()
    )
    for notification in pending:
        notification.status = NotificationStatus.CANCELLED
        notification.cancelled_at = consent.revoked_at
        record_event(
            session,
            actor_id=str(user.id),
            action="notification.cancelled_consent_revoked",
            resource_type="notification",
            resource_id=notification.id,
        )
    record_event(session, actor_id=str(user.id), action="notification_consent.revoked", resource_type="notification_consent", resource_id=consent.id)
    await session.commit()
    await session.refresh(consent)
    return consent


@router.get("/notifications", response_model=list[NotificationRead])
async def list_notifications(patient_id: UUID, user: Staff, session: Db) -> list[Notification]:
    await patient_or_404(session, patient_id)
    notifications = list((await session.scalars(select(Notification).where(Notification.patient_id == patient_id).order_by(Notification.created_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="notifications.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return notifications


@router.post("/notifications", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(patient_id: UUID, payload: NotificationCreate, user: Staff, session: Db) -> Notification:
    patient = await patient_or_404(session, patient_id)
    consent = await latest_consent(session, patient_id, payload.channel)
    if consent is None or consent.status != ConsentStatus.GRANTED:
        raise ConflictError("Explicit opt-in is required for this notification channel")
    if payload.appointment_id is not None:
        appointment = await session.get(Appointment, payload.appointment_id)
        if appointment is None or appointment.patient_id != patient_id:
            raise NotFoundError("Appointment not found for patient")
    recipient = payload.recipient or patient.phone
    if recipient is None or not PHONE_RE.fullmatch(recipient):
        raise ConflictError("Patient phone must use E.164 format")
    notification = Notification(patient_id=patient_id, appointment_id=payload.appointment_id, created_by=user.id, channel=payload.channel, recipient=recipient, template_key=payload.template_key, message=payload.message)
    session.add(notification)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="notification.queued", resource_type="notification", resource_id=notification.id)
    await session.commit()
    await session.refresh(notification)
    return notification


@router.post("/notifications/{notification_id}/cancel", response_model=NotificationRead)
async def cancel_notification(patient_id: UUID, notification_id: UUID, user: Staff, session: Db) -> Notification:
    notification = await notification_or_404(session, patient_id, notification_id, lock=True)
    if notification.status != NotificationStatus.PENDING:
        raise ConflictError("Only pending notifications can be cancelled")
    notification.status = NotificationStatus.CANCELLED
    notification.cancelled_at = utc_now()
    record_event(session, actor_id=str(user.id), action="notification.cancelled", resource_type="notification", resource_id=notification.id)
    await session.commit()
    await session.refresh(notification)
    return notification


@router.post("/notifications/{notification_id}/result", response_model=NotificationRead)
async def record_notification_result(patient_id: UUID, notification_id: UUID, payload: NotificationResult, user: InternalAdmin, session: Db) -> Notification:
    notification = await notification_or_404(session, patient_id, notification_id, lock=True)
    if notification.status != NotificationStatus.PENDING:
        raise ConflictError("Only pending notifications can receive a delivery result")
    notification.status = payload.status
    notification.processed_at = utc_now()
    notification.provider_reference = payload.provider_reference
    notification.failure_code = payload.failure_code
    record_event(session, actor_id=str(user.id), action=f"notification.{payload.status.value}", resource_type="notification", resource_id=notification.id)
    await session.commit()
    await session.refresh(notification)
    return notification
