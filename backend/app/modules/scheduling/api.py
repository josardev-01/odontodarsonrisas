from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.models import Patient
from app.modules.professionals.models import Professional
from app.modules.scheduling.models import Appointment, AppointmentStatus
from app.modules.scheduling.schemas import AppointmentCreate, AppointmentRead, AppointmentReschedule, AppointmentStatusUpdate
from app.platform.database import get_session
from app.platform.errors import ConflictError, NotFoundError

router = APIRouter(prefix="/appointments", tags=["scheduling"])
Staff = Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))]
Db = Annotated[AsyncSession, Depends(get_session)]


def as_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


async def ensure_references(session: AsyncSession, payload: AppointmentCreate) -> None:
    patient = await session.get(Patient, payload.patient_id)
    professional = await session.get(Professional, payload.professional_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")
    if professional is None or not professional.active:
        raise NotFoundError("Active professional not found")


async def ensure_available(
    session: AsyncSession,
    *,
    professional_id: UUID,
    starts_at: datetime,
    ends_at: datetime,
    excluding_id: UUID | None = None,
) -> None:
    statement = select(Appointment.id).where(
            Appointment.professional_id == professional_id,
            Appointment.status == AppointmentStatus.SCHEDULED,
            Appointment.starts_at < as_utc(ends_at),
            Appointment.ends_at > as_utc(starts_at),
        )
    if excluding_id is not None:
        statement = statement.where(Appointment.id != excluding_id)
    overlapping = await session.scalar(statement.limit(1))
    if overlapping is not None:
        raise ConflictError("The professional already has an appointment in that time window")


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(payload: AppointmentCreate, user: Staff, session: Db) -> Appointment:
    await ensure_references(session, payload)
    await ensure_available(
        session,
        professional_id=payload.professional_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )
    values = payload.model_dump()
    values["starts_at"] = as_utc(payload.starts_at)
    values["ends_at"] = as_utc(payload.ends_at)
    appointment = Appointment(**values)
    session.add(appointment)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("The professional already has an appointment in that time window") from exc
    record_event(session, actor_id=str(user.id), action="appointment.created", resource_type="appointment", resource_id=appointment.id)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("The professional already has an appointment in that time window") from exc
    await session.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/schedule", response_model=AppointmentRead)
async def reschedule_appointment(
    appointment_id: UUID,
    payload: AppointmentReschedule,
    user: Staff,
    session: Db,
) -> Appointment:
    appointment = await session.get(Appointment, appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found")
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise ConflictError("Only scheduled appointments can be rescheduled")
    await ensure_available(
        session,
        professional_id=appointment.professional_id,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        excluding_id=appointment.id,
    )
    appointment.starts_at = as_utc(payload.starts_at)
    appointment.ends_at = as_utc(payload.ends_at)
    record_event(
        session,
        actor_id=str(user.id),
        action="appointment.rescheduled",
        resource_type="appointment",
        resource_id=appointment.id,
    )
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("The professional already has an appointment in that time window") from exc
    await session.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
async def change_appointment_status(
    appointment_id: UUID,
    payload: AppointmentStatusUpdate,
    user: Staff,
    session: Db,
) -> Appointment:
    appointment = await session.get(Appointment, appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found")
    if appointment.status != AppointmentStatus.SCHEDULED:
        raise ConflictError("Only scheduled appointments can change status")
    if payload.status not in {AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED}:
        raise ConflictError("A scheduled appointment can only be cancelled or completed")
    appointment.status = payload.status
    record_event(
        session,
        actor_id=str(user.id),
        action=f"appointment.{payload.status.value}",
        resource_type="appointment",
        resource_id=appointment.id,
    )
    await session.commit()
    await session.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    user: Staff,
    session: Db,
    from_: Annotated[datetime, Query(alias="from")],
    to: Annotated[datetime, Query()],
    professional_id: UUID | None = None,
) -> list[Appointment]:
    statement = select(Appointment).where(
        Appointment.starts_at >= as_utc(from_), Appointment.starts_at < as_utc(to)
    ).order_by(Appointment.starts_at)
    if professional_id:
        statement = statement.where(Appointment.professional_id == professional_id)
    return list((await session.scalars(statement)).all())
