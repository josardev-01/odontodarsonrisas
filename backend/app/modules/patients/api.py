from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate, PatientRead, PatientUpdate
from app.platform.database import get_session
from app.platform.errors import ConflictError, NotFoundError

router = APIRouter(prefix="/patients", tags=["patients"])
Staff = Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))]
PatientReader = Annotated[CurrentUser, Depends(require_roles("admin", "recepcion", "profesional"))]
Db = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(payload: PatientCreate, user: Staff, session: Db) -> Patient:
    patient = Patient(**payload.model_dump())
    session.add(patient)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("A patient with that document already exists") from exc
    record_event(session, actor_id=str(user.id), action="patient.created", resource_type="patient", resource_id=patient.id)
    await session.commit()
    await session.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead])
async def list_patients(
    user: PatientReader,
    session: Db,
    query: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[Patient]:
    statement = select(Patient).order_by(Patient.last_name, Patient.first_name).limit(limit)
    if query:
        pattern = f"%{query}%"
        statement = statement.where(or_(Patient.first_name.ilike(pattern), Patient.last_name.ilike(pattern)))
    return list((await session.scalars(statement)).all())


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(patient_id: UUID, user: PatientReader, session: Db) -> Patient:
    patient = await session.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found")
    record_event(session, actor_id=str(user.id), action="patient.viewed", resource_type="patient", resource_id=patient.id)
    await session.commit()
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
async def update_patient(patient_id: UUID, payload: PatientUpdate, user: Staff, session: Db) -> Patient:
    patient = await session.get(Patient, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found")
    for key, value in payload.model_dump().items():
        setattr(patient, key, value)
    record_event(session, actor_id=str(user.id), action="patient.updated", resource_type="patient", resource_id=patient.id)
    await session.commit()
    await session.refresh(patient)
    return patient
