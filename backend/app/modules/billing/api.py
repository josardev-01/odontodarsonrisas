from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.audit.service import record_event
from app.modules.billing.models import Invoice, InvoiceStatus, Payment
from app.modules.billing.schemas import BillablePlanRead, InvoiceCreate, InvoiceRead, PaymentCreate
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.models import Patient
from app.modules.treatment_plans.models import PlanStatus, TreatmentPlan
from app.platform.database import get_session
from app.platform.errors import ConflictError, NotFoundError
from app.platform.types import utc_now

router = APIRouter(prefix="/patients/{patient_id}/invoices", tags=["billing"])
Db = Annotated[AsyncSession, Depends(get_session)]
FinancialStaff = Annotated[CurrentUser, Depends(require_roles("admin", "recepcion"))]


async def patient_or_404(session: AsyncSession, patient_id: UUID) -> None:
    patient = await session.get(Patient, patient_id)
    if patient is None or not patient.active:
        raise NotFoundError("Active patient not found")


async def invoice_or_404(session: AsyncSession, patient_id: UUID, invoice_id: UUID, *, lock: bool = False) -> Invoice:
    statement = select(Invoice).options(selectinload(Invoice.payments)).where(Invoice.id == invoice_id, Invoice.patient_id == patient_id)
    if lock:
        statement = statement.with_for_update()
    invoice = await session.scalar(statement)
    if invoice is None:
        raise NotFoundError("Invoice not found")
    return invoice


def plan_total(plan: TreatmentPlan) -> Decimal:
    return sum((item.unit_price * item.quantity for item in plan.items), Decimal(0))


@router.get("/billable-plans", response_model=list[BillablePlanRead])
async def list_billable_plans(patient_id: UUID, user: FinancialStaff, session: Db) -> list[BillablePlanRead]:
    await patient_or_404(session, patient_id)
    plans = list((await session.scalars(select(TreatmentPlan).options(selectinload(TreatmentPlan.items)).where(TreatmentPlan.patient_id == patient_id, TreatmentPlan.status.in_([PlanStatus.ACCEPTED, PlanStatus.IN_PROGRESS, PlanStatus.COMPLETED]), ~TreatmentPlan.id.in_(select(Invoice.treatment_plan_id))).order_by(TreatmentPlan.created_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="billable_plans.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return [BillablePlanRead(id=plan.id, title=plan.title, total=plan_total(plan)) for plan in plans]


@router.get("", response_model=list[InvoiceRead])
async def list_invoices(patient_id: UUID, user: FinancialStaff, session: Db) -> list[Invoice]:
    await patient_or_404(session, patient_id)
    invoices = list((await session.scalars(select(Invoice).options(selectinload(Invoice.payments)).where(Invoice.patient_id == patient_id).order_by(Invoice.created_at.desc()))).all())
    record_event(session, actor_id=str(user.id), action="invoices.viewed", resource_type="patient", resource_id=patient_id)
    await session.commit()
    return invoices


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(patient_id: UUID, payload: InvoiceCreate, user: FinancialStaff, session: Db) -> Invoice:
    await patient_or_404(session, patient_id)
    plan = await session.scalar(select(TreatmentPlan).options(selectinload(TreatmentPlan.items)).where(TreatmentPlan.id == payload.treatment_plan_id, TreatmentPlan.patient_id == patient_id))
    if plan is None:
        raise NotFoundError("Treatment plan not found")
    if plan.status not in {PlanStatus.ACCEPTED, PlanStatus.IN_PROGRESS, PlanStatus.COMPLETED}:
        raise ConflictError("Only accepted treatment plans can be billed")
    amount = plan_total(plan)
    if amount <= 0:
        raise ConflictError("A zero-value treatment plan cannot be billed")
    invoice = Invoice(patient_id=patient_id, treatment_plan_id=plan.id, created_by=user.id, number=f"DS-{utc_now():%Y%m%d}-{uuid4().hex[:8].upper()}", description=plan.title, amount=amount, currency="PYG", due_date=payload.due_date)
    session.add(invoice)
    try:
        await session.flush()
        record_event(session, actor_id=str(user.id), action="invoice.created", resource_type="invoice", resource_id=invoice.id)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("The treatment plan already has an invoice") from exc
    return await invoice_or_404(session, patient_id, invoice.id)


@router.post("/{invoice_id}/payments", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def add_payment(patient_id: UUID, invoice_id: UUID, payload: PaymentCreate, user: FinancialStaff, session: Db) -> Invoice:
    invoice = await invoice_or_404(session, patient_id, invoice_id, lock=True)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ConflictError("A cancelled invoice cannot receive payments")
    paid = sum((payment.amount for payment in invoice.payments), Decimal(0))
    if payload.amount > invoice.amount - paid:
        raise ConflictError("Payment exceeds the outstanding balance")
    payment = Payment(invoice_id=invoice.id, recorded_by=user.id, **payload.model_dump())
    invoice.payments.append(payment)
    new_paid = paid + payload.amount
    invoice.status = InvoiceStatus.PAID if new_paid == invoice.amount else InvoiceStatus.PARTIALLY_PAID
    await session.flush()
    record_event(session, actor_id=str(user.id), action="payment.recorded", resource_type="invoice", resource_id=invoice.id)
    await session.commit()
    return await invoice_or_404(session, patient_id, invoice.id)


@router.post("/{invoice_id}/cancel", response_model=InvoiceRead)
async def cancel_invoice(patient_id: UUID, invoice_id: UUID, user: FinancialStaff, session: Db) -> Invoice:
    invoice = await invoice_or_404(session, patient_id, invoice_id, lock=True)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ConflictError("Invoice is already cancelled")
    if invoice.payments:
        raise ConflictError("An invoice with payments cannot be cancelled; record a refund in a future accounting workflow")
    invoice.status = InvoiceStatus.CANCELLED
    invoice.cancelled_at = utc_now()
    record_event(session, actor_id=str(user.id), action="invoice.cancelled", resource_type="invoice", resource_id=invoice.id)
    await session.commit()
    return await invoice_or_404(session, patient_id, invoice.id)
