from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.evolution.models import EvolutionEntry
from app.modules.evolution.schemas import EvolutionEntryCreate, EvolutionEntryRead
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.odontogram.models import OdontogramWorkItem
from app.modules.patients.models import Patient
from app.modules.treatment_plans.models import PlanStatus, TreatmentPlan, TreatmentPlanItem
from app.platform.database import get_session
from app.platform.errors import ConflictError, NotFoundError
from app.platform.types import utc_now

router = APIRouter(prefix="/patients/{patient_id}/evolution", tags=["evolution"])
Db = Annotated[AsyncSession, Depends(get_session)]
ClinicalStaff = Annotated[CurrentUser, Depends(require_roles("admin", "profesional"))]


async def work_or_404(session: AsyncSession, patient_id: UUID, work_item_id: UUID, *, lock: bool = False) -> OdontogramWorkItem:
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")
    query = select(OdontogramWorkItem).where(OdontogramWorkItem.id == work_item_id, OdontogramWorkItem.patient_id == patient_id)
    if lock:
        query = query.with_for_update()
    work = await session.scalar(query)
    if work is None:
        raise NotFoundError("Odontogram work item not found")
    return work


async def active_plan_item(session: AsyncSession, work: OdontogramWorkItem) -> tuple[TreatmentPlan, TreatmentPlanItem]:
    if work.current_plan_id is None or work.completed_at is not None:
        raise ConflictError("The odontogram work item is not active in a plan")
    plan = await session.get(TreatmentPlan, work.current_plan_id)
    if plan is None or plan.status not in {PlanStatus.ACCEPTED, PlanStatus.IN_PROGRESS}:
        raise ConflictError("The treatment plan must be accepted before recording evolution")
    item = await session.scalar(select(TreatmentPlanItem).where(
        TreatmentPlanItem.plan_id == plan.id, TreatmentPlanItem.work_item_id == work.id
    ))
    if item is None:
        raise ConflictError("The procedure is missing from its treatment plan")
    return plan, item


@router.get("/entries", response_model=list[EvolutionEntryRead])
async def list_entries(patient_id: UUID, user: ClinicalStaff, session: Db):
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")
    entries = list((await session.scalars(select(EvolutionEntry)
        .where(EvolutionEntry.patient_id == patient_id)
        .order_by(EvolutionEntry.created_at.desc(), EvolutionEntry.id.desc())
    )).all())
    record_event(session, actor_id=str(user.id), action="evolution.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return entries


@router.post("/work-items/{work_item_id}/entries", response_model=EvolutionEntryRead, status_code=status.HTTP_201_CREATED)
async def record_evolution(patient_id: UUID, work_item_id: UUID, payload: EvolutionEntryCreate, user: ClinicalStaff, session: Db):
    work = await work_or_404(session, patient_id, work_item_id, lock=True)
    plan, item = await active_plan_item(session, work)
    entry = EvolutionEntry(
        patient_id=patient_id, work_item_id=work.id, plan_item_id=item.id,
        recorded_by=user.id, answers=[], control_completed=payload.control_completed,
        notes=None if payload.control_completed else payload.notes.strip(),
    )
    session.add(entry)
    if plan.status == PlanStatus.ACCEPTED:
        plan.status = PlanStatus.IN_PROGRESS
    if payload.control_completed:
        work.completed_at = utc_now()
        work.completed_by = user.id
        others = await session.scalar(select(OdontogramWorkItem.id)
            .where(OdontogramWorkItem.current_plan_id == plan.id, OdontogramWorkItem.id != work.id, OdontogramWorkItem.completed_at.is_(None))
            .limit(1))
        if others is None and all(plan_item.work_item_id is not None for plan_item in plan.items):
            plan.status = PlanStatus.COMPLETED
    await session.flush()
    record_event(session, actor_id=str(user.id), action="evolution.recorded", resource_type="evolution_entry", resource_id=entry.id)
    if payload.control_completed:
        record_event(session, actor_id=str(user.id), action="evolution.procedure_completed", resource_type="odontogram_work_item", resource_id=work.id)
    await session.commit()
    await session.refresh(entry)
    return entry
