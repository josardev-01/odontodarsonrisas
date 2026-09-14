from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.service import record_event
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.models import Patient
from app.modules.treatment_plans.models import PlanStatus, TreatmentPlan, TreatmentPlanItem
from app.modules.treatment_plans.schemas import PlanCreate, PlanItemCreate, PlanRead, PlanStatusChange
from app.modules.treatments.models import Treatment
from app.platform.database import get_session
from app.platform.errors import ConflictError, NotFoundError
from app.platform.types import utc_now

router = APIRouter(prefix="/patients/{patient_id}/treatment-plans", tags=["treatment-plans"])
Db = Annotated[AsyncSession, Depends(get_session)]
ClinicalStaff = Annotated[CurrentUser, Depends(require_roles("admin", "profesional"))]

TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.DRAFT: {PlanStatus.PROPOSED, PlanStatus.CANCELLED},
    PlanStatus.PROPOSED: {PlanStatus.ACCEPTED, PlanStatus.REJECTED, PlanStatus.CANCELLED},
    PlanStatus.ACCEPTED: {PlanStatus.IN_PROGRESS, PlanStatus.CANCELLED},
    PlanStatus.IN_PROGRESS: {PlanStatus.COMPLETED, PlanStatus.CANCELLED},
    PlanStatus.REJECTED: set(),
    PlanStatus.COMPLETED: set(),
    PlanStatus.CANCELLED: set(),
}


async def patient_or_404(session: AsyncSession, patient_id: UUID) -> None:
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")


async def plan_or_404(session: AsyncSession, patient_id: UUID, plan_id: UUID) -> TreatmentPlan:
    plan = await session.scalar(select(TreatmentPlan).options(selectinload(TreatmentPlan.items)).where(TreatmentPlan.id == plan_id, TreatmentPlan.patient_id == patient_id))
    if plan is None:
        raise NotFoundError("Treatment plan not found")
    return plan


@router.get("", response_model=list[PlanRead])
async def list_plans(patient_id: UUID, user: ClinicalStaff, session: Db) -> list[TreatmentPlan]:
    await patient_or_404(session, patient_id)
    plans = list((await session.scalars(select(TreatmentPlan).options(selectinload(TreatmentPlan.items)).where(TreatmentPlan.patient_id == patient_id).order_by(TreatmentPlan.created_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="treatment_plans.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return plans


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(patient_id: UUID, payload: PlanCreate, user: ClinicalStaff, session: Db) -> TreatmentPlan:
    await patient_or_404(session, patient_id)
    plan = TreatmentPlan(patient_id=patient_id, created_by=user.id, **payload.model_dump())
    session.add(plan)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="treatment_plan.created", resource_type="treatment_plan", resource_id=plan.id)
    await session.commit()
    return await plan_or_404(session, patient_id, plan.id)


@router.post("/{plan_id}/items", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def add_item(patient_id: UUID, plan_id: UUID, payload: PlanItemCreate, user: ClinicalStaff, session: Db) -> TreatmentPlan:
    plan = await plan_or_404(session, patient_id, plan_id)
    if plan.status != PlanStatus.DRAFT:
        raise ConflictError("Items can only be added to a draft plan")
    treatment = await session.get(Treatment, payload.treatment_id)
    if treatment is None or not treatment.active:
        raise NotFoundError("Active treatment not found")
    item = TreatmentPlanItem(
        plan_id=plan.id,
        treatment_id=treatment.id,
        tooth_code=payload.tooth_code,
        treatment_code=treatment.code,
        description=treatment.name,
        quantity=payload.quantity,
        unit_price=payload.unit_price if payload.unit_price is not None else treatment.default_price,
        currency="PYG",
    )
    plan.items.append(item)
    await session.flush()
    record_event(session, actor_id=str(user.id), action="treatment_plan.item_added", resource_type="treatment_plan", resource_id=plan.id)
    await session.commit()
    return await plan_or_404(session, patient_id, plan.id)


@router.patch("/{plan_id}/status", response_model=PlanRead)
async def change_status(patient_id: UUID, plan_id: UUID, payload: PlanStatusChange, user: ClinicalStaff, session: Db) -> TreatmentPlan:
    plan = await plan_or_404(session, patient_id, plan_id)
    if payload.status not in TRANSITIONS[plan.status]:
        raise ConflictError(f"Invalid treatment plan transition from {plan.status.value} to {payload.status.value}")
    if payload.status == PlanStatus.PROPOSED and not plan.items:
        raise ConflictError("A plan without items cannot be proposed")
    plan.status = payload.status
    if payload.status == PlanStatus.ACCEPTED:
        plan.accepted_at = utc_now()
    record_event(session, actor_id=str(user.id), action="treatment_plan.status_changed", resource_type="treatment_plan", resource_id=plan.id)
    await session.commit()
    return await plan_or_404(session, patient_id, plan.id)
