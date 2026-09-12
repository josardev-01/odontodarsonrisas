from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.clinical_schemas import (
    ClinicalEntryCreate,
    ClinicalEntryRead,
    ClinicalProfileRead,
    ClinicalProfileWrite,
    ConsentCreate,
    ConsentRead,
)
from app.modules.patients.models import ClinicalEntry, ClinicalProfile, ConsentRecord, Patient
from app.platform.database import get_session
from app.platform.errors import NotFoundError
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
