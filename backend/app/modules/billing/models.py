from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.database import Base
from app.platform.types import EntityMixin


class InvoiceStatus(StrEnum):
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


class Invoice(EntityMixin, Base):
    __tablename__ = "invoices"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    treatment_plan_id: Mapped[UUID] = mapped_column(ForeignKey("treatment_plans.id", ondelete="RESTRICT"), unique=True, index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    currency: Mapped[str] = mapped_column(String(3), default="PYG")
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus, native_enum=False, length=30), default=InvoiceStatus.ISSUED, index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")


class Payment(EntityMixin, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id", ondelete="RESTRICT"), index=True)
    invoice: Mapped[Invoice] = relationship(back_populates="payments")
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, native_enum=False, length=20))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reference: Mapped[str | None] = mapped_column(String(120))
