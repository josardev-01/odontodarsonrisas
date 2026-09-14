from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.odontogram.models import OdontogramEvent
from app.modules.odontogram.schemas import OdontogramEventCreate, OdontogramEventRead
from app.modules.patients.models import Patient
from app.modules.treatments.models import Treatment
from app.platform.database import get_session
from app.platform.errors import NotFoundError

router = APIRouter(prefix="/patients/{patient_id}/odontogram", tags=["odontogram"])
Db = Annotated[AsyncSession, Depends(get_session)]
ClinicalStaff = Annotated[CurrentUser, Depends(require_roles("admin", "profesional"))]


async def ensure_references(session: AsyncSession, patient_id: UUID, treatment_id: UUID | None) -> None:
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")
    if treatment_id is not None:
        treatment = await session.get(Treatment, treatment_id)
        if treatment is None or not treatment.active:
            raise NotFoundError("Active treatment not found")


@router.get("/history", response_model=list[OdontogramEventRead])
async def history(patient_id: UUID, user: ClinicalStaff, session: Db) -> list[OdontogramEvent]:
    await ensure_references(session, patient_id, None)
    items = list((await session.scalars(select(OdontogramEvent).where(OdontogramEvent.patient_id == patient_id).order_by(OdontogramEvent.observed_at.desc(), OdontogramEvent.created_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="odontogram.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return items


@router.get("/current", response_model=list[OdontogramEventRead])
async def current(patient_id: UUID, user: ClinicalStaff, session: Db) -> list[OdontogramEvent]:
    await ensure_references(session, patient_id, None)
    items = list((await session.scalars(select(OdontogramEvent).where(OdontogramEvent.patient_id == patient_id).order_by(OdontogramEvent.observed_at.desc(), OdontogramEvent.created_at.desc()))).all())
    latest: dict[tuple[str, str], OdontogramEvent] = {}
    for item in items:
        latest.setdefault((item.tooth_code, item.surface.value), item)
    record_event(session, actor_id=str(user.id), action="odontogram.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return list(latest.values())


@router.post("/events", response_model=OdontogramEventRead, status_code=status.HTTP_201_CREATED)
async def record_condition(patient_id: UUID, payload: OdontogramEventCreate, user: ClinicalStaff, session: Db) -> OdontogramEvent:
    await ensure_references(session, patient_id, payload.treatment_id)
    event = OdontogramEvent(patient_id=patient_id, recorded_by=user.id, **payload.model_dump())
    session.add(event)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="odontogram.condition_recorded", resource_type="odontogram_event", resource_id=event.id)
    await session.commit()
    await session.refresh(event)
    return event
