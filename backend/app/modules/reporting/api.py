from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import record_event
from app.modules.billing.models import Invoice, InvoiceStatus, Payment
from app.modules.identity.api import CurrentUser, require_roles
from app.modules.patients.models import Patient
from app.modules.reporting.schemas import AdministrativeSummary, InvoiceStatusCounts
from app.modules.scheduling.models import Appointment, AppointmentStatus
from app.platform.database import get_session
from app.platform.types import utc_now

ASUNCION = ZoneInfo("America/Asuncion")
MAX_RANGE_DAYS = 366

router = APIRouter(prefix="/admin/reports", tags=["reporting"])
Db = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[CurrentUser, Depends(require_roles("admin"))]


def _parse_boundary(raw: str, *, end: bool) -> tuple[datetime, date]:
    """Return an exclusive UTC boundary and its local reporting date."""
    try:
        parsed_date = date.fromisoformat(raw)
    except ValueError:
        try:
            parsed_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="from and to must be ISO dates or timezone-aware ISO timestamps") from exc
        if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
            raise HTTPException(status_code=422, detail="ISO timestamps must include a timezone")
        local_at = parsed_at.astimezone(ASUNCION)
        return parsed_at.astimezone(timezone.utc), local_at.date()

    local_boundary = datetime.combine(parsed_date + (timedelta(days=1) if end else timedelta()), time.min, ASUNCION)
    return local_boundary.astimezone(timezone.utc), parsed_date


def reporting_window(from_value: str, to_value: str) -> tuple[datetime, datetime, date, date]:
    starts_at, from_date = _parse_boundary(from_value, end=False)
    ends_at, to_date = _parse_boundary(to_value, end=True)
    if ends_at <= starts_at:
        raise HTTPException(status_code=422, detail="to must be on or after from")
    if ends_at - starts_at > timedelta(days=MAX_RANGE_DAYS):
        raise HTTPException(status_code=422, detail=f"Reporting range cannot exceed {MAX_RANGE_DAYS} days")
    return starts_at, ends_at, from_date, to_date


@router.get("/summary", response_model=AdministrativeSummary)
async def administrative_summary(
    user: Admin,
    session: Db,
    from_value: Annotated[str, Query(alias="from", description="ISO date or timezone-aware ISO timestamp")],
    to_value: Annotated[str, Query(alias="to", description="ISO date or timezone-aware ISO timestamp")],
) -> AdministrativeSummary:
    starts_at, ends_at, from_date, to_date = reporting_window(from_value, to_value)
    now = utc_now()

    active_patients = int(await session.scalar(select(func.count(Patient.id)).where(Patient.active.is_(True))) or 0)

    appointment_counts = (
        await session.execute(
            select(
                func.count(Appointment.id).filter(Appointment.starts_at >= starts_at, Appointment.starts_at < ends_at),
                func.count(Appointment.id).filter(
                    Appointment.starts_at >= now,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                ),
            )
        )
    ).one()

    collected_amount = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.paid_at >= starts_at, Payment.paid_at < ends_at)
    )

    paid_by_invoice = select(Payment.invoice_id, func.sum(Payment.amount).label("paid_amount")).group_by(Payment.invoice_id).subquery()
    invoice_rows = (
        await session.execute(
            select(
                Invoice.status,
                func.count(Invoice.id),
                func.coalesce(
                    func.sum(
                        case(
                            (Invoice.status != InvoiceStatus.CANCELLED, Invoice.amount - func.coalesce(paid_by_invoice.c.paid_amount, 0)),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .outerjoin(paid_by_invoice, paid_by_invoice.c.invoice_id == Invoice.id)
            .group_by(Invoice.status)
        )
    ).all()
    status_counts = {status.value: int(count) for status, count, _ in invoice_rows}
    outstanding_balance = sum((Decimal(balance) for _, _, balance in invoice_rows), Decimal(0))

    record_event(
        session,
        actor_id=str(user.id),
        action="administrative_report.viewed",
        resource_type="report",
        resource_id=None,
        detail=f"from={starts_at.isoformat()};to_exclusive={ends_at.isoformat()}",
    )
    await session.commit()

    return AdministrativeSummary(
        from_date=from_date,
        to_date=to_date,
        active_patients=active_patients,
        appointments_in_range=int(appointment_counts[0] or 0),
        upcoming_appointments=int(appointment_counts[1] or 0),
        collected_amount=Decimal(collected_amount),
        outstanding_balance=outstanding_balance,
        invoices_by_status=InvoiceStatusCounts(**status_counts),
    )
