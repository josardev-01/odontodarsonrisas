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
from app.modules.patients.clinical_schemas import (
    ClinicalEntryCreate,
    ClinicalEntryRead,
    ClinicalHistoryDocumentRead,
    ClinicalProfileRead,
    ClinicalProfileWrite,
    ConsentCreate,
    ConsentRead,
)
from app.modules.patients.models import ClinicalEntry, ClinicalHistoryDocument, ClinicalProfile, ConsentRecord, Patient
from app.platform.database import get_session
from app.platform.attachments import attachment_response, read_signed_attachment, store_attachment
from app.platform.errors import ConflictError, NotFoundError
from app.platform.types import utc_now

router = APIRouter(prefix="/patients/{patient_id}", tags=["clinical-history"])
Db = Annotated[AsyncSession, Depends(get_session)]
ClinicalStaff = Annotated[CurrentUser, Depends(require_roles("admin", "profesional"))]
ConsentStaff = Annotated[CurrentUser, Depends(require_roles("admin", "profesional", "recepcion"))]


async def ensure_patient(session: AsyncSession, patient_id: UUID) -> None:
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")


@router.get("/clinical-profile", response_model=ClinicalProfileRead | None)
async def get_clinical_profile(patient_id: UUID, user: ClinicalStaff, session: Db):
    await ensure_patient(session, patient_id)
    profile = await session.scalar(select(ClinicalProfile).where(ClinicalProfile.patient_id == patient_id))
    record_event(session, actor_id=str(user.id), action="clinical_profile.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return profile


@router.put("/clinical-profile", response_model=ClinicalProfileRead)
async def upsert_clinical_profile(patient_id: UUID, payload: ClinicalProfileWrite, user: ClinicalStaff, session: Db):
    await ensure_patient(session, patient_id)
    profile = await session.scalar(select(ClinicalProfile).where(ClinicalProfile.patient_id == patient_id))
    values = payload.model_dump()
    if profile is None:
        profile = ClinicalProfile(patient_id=patient_id, updated_by=user.id, updated_at=utc_now(), **values)
        session.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
        profile.updated_by = user.id
        profile.updated_at = utc_now()
    record_event(session, actor_id=str(user.id), action="clinical_profile.updated", resource_type="patient", resource_id=patient_id)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.get("/clinical-entries", response_model=list[ClinicalEntryRead])
async def list_clinical_entries(patient_id: UUID, user: ClinicalStaff, session: Db):
    await ensure_patient(session, patient_id)
    entries = list((await session.scalars(select(ClinicalEntry).where(ClinicalEntry.patient_id == patient_id).order_by(ClinicalEntry.occurred_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="clinical_history.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return entries


@router.post("/clinical-entries", response_model=ClinicalEntryRead, status_code=status.HTTP_201_CREATED)
async def create_clinical_entry(patient_id: UUID, payload: ClinicalEntryCreate, user: ClinicalStaff, session: Db):
    await ensure_patient(session, patient_id)
    entry = ClinicalEntry(patient_id=patient_id, author_id=user.id, **payload.model_dump())
    session.add(entry)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="clinical_entry.created", resource_type="clinical_entry", resource_id=entry.id)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.get("/clinical-history-documents", response_model=list[ClinicalHistoryDocumentRead])
async def list_clinical_history_documents(patient_id: UUID, user: ClinicalStaff, session: Db):
    await ensure_patient(session, patient_id)
    documents = list((await session.scalars(
        select(ClinicalHistoryDocument)
        .where(ClinicalHistoryDocument.patient_id == patient_id)
        .order_by(ClinicalHistoryDocument.created_at.desc(), ClinicalHistoryDocument.id.desc())
    )).all())
    record_event(session, actor_id=str(user.id), action="clinical_history_documents.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return documents


@router.post("/clinical-history-documents", response_model=ClinicalHistoryDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_clinical_history_document(
    patient_id: UUID,
    attachment: Annotated[UploadFile, File()],
    user: ClinicalStaff,
    session: Db,
):
    await ensure_patient(session, patient_id)
    document = ClinicalHistoryDocument(patient_id=patient_id, uploaded_by=user.id)
    store_attachment(document, await read_signed_attachment(attachment))
    session.add(document)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="clinical_history_document.uploaded", resource_type="clinical_history_document", resource_id=document.id)
    await session.commit()
    await session.refresh(document)
    return document


@router.get("/clinical-history-documents/{document_id}/attachment")
async def download_clinical_history_document(patient_id: UUID, document_id: UUID, user: ClinicalStaff, session: Db) -> Response:
    await ensure_patient(session, patient_id)
    document = await session.scalar(
        select(ClinicalHistoryDocument)
        .options(undefer(ClinicalHistoryDocument.attachment_data))
        .where(ClinicalHistoryDocument.id == document_id, ClinicalHistoryDocument.patient_id == patient_id)
    )
    if document is None:
        raise NotFoundError("Clinical history document not found")
    response = attachment_response(document)
    record_event(session, actor_id=str(user.id), action="clinical_history_document.downloaded", resource_type="clinical_history_document", resource_id=document.id)
    await session.commit()
    return response


@router.get("/consents", response_model=list[ConsentRead])
async def list_consents(patient_id: UUID, user: ConsentStaff, session: Db):
    await ensure_patient(session, patient_id)
    records = list((await session.scalars(select(ConsentRecord).where(ConsentRecord.patient_id == patient_id).order_by(ConsentRecord.signed_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="consent_metadata.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return records


@router.post("/consents", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
async def create_consent(patient_id: UUID, payload: ConsentCreate, user: ConsentStaff, session: Db):
    await ensure_patient(session, patient_id)
    record = ConsentRecord(patient_id=patient_id, recorded_by=user.id, **payload.model_dump())
    session.add(record)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="consent.recorded", resource_type="consent", resource_id=record.id)
    await session.commit()
    await session.refresh(record)
    return record


@router.post("/consents/with-attachment", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
async def create_consent_with_attachment(
    patient_id: UUID,
    metadata: Annotated[str, Form()],
    attachment: Annotated[UploadFile, File()],
    user: ConsentStaff,
    session: Db,
):
    await ensure_patient(session, patient_id)
    try:
        payload = ConsentCreate.model_validate_json(metadata)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid consent metadata") from exc
    document = await read_signed_attachment(attachment)
    record = ConsentRecord(patient_id=patient_id, recorded_by=user.id, **payload.model_dump())
    store_attachment(record, document)
    session.add(record)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="consent.recorded_with_attachment", resource_type="consent", resource_id=record.id)
    await session.commit()
    await session.refresh(record)
    return record


@router.put("/consents/{consent_id}/attachment", response_model=ConsentRead)
async def attach_consent_document(
    patient_id: UUID,
    consent_id: UUID,
    attachment: Annotated[UploadFile, File()],
    user: ConsentStaff,
    session: Db,
):
    await ensure_patient(session, patient_id)
    record = await session.scalar(
        select(ConsentRecord).where(ConsentRecord.id == consent_id, ConsentRecord.patient_id == patient_id).with_for_update()
    )
    if record is None:
        raise NotFoundError("Consent not found")
    if record.attachment_filename is not None:
        raise ConflictError("A signed document is already attached to this consent")
    store_attachment(record, await read_signed_attachment(attachment))
    record_event(session, actor_id=str(user.id), action="consent.attachment_added", resource_type="consent", resource_id=record.id)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/consents/{consent_id}/attachment")
async def download_consent_document(patient_id: UUID, consent_id: UUID, user: ConsentStaff, session: Db) -> Response:
    await ensure_patient(session, patient_id)
    record = await session.scalar(
        select(ConsentRecord)
        .options(undefer(ConsentRecord.attachment_data))
        .where(ConsentRecord.id == consent_id, ConsentRecord.patient_id == patient_id)
    )
    if record is None:
        raise NotFoundError("Consent not found")
    response = attachment_response(record)
    record_event(session, actor_id=str(user.id), action="consent.attachment_downloaded", resource_type="consent", resource_id=record.id)
    await session.commit()
    return response
