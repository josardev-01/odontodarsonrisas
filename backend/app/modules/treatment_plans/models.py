from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.database import Base
from app.platform.types import EntityMixin


class PlanStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TreatmentPlan(EntityMixin, Base):
    __tablename__ = "treatment_plans"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    clinical_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PlanStatus] = mapped_column(Enum(PlanStatus, native_enum=False, length=30), default=PlanStatus.DRAFT, index=True)
    valid_until: Mapped[date | None] = mapped_column(Date)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items: Mapped[list["TreatmentPlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan", lazy="selectin")


class TreatmentPlanItem(EntityMixin, Base):
    __tablename__ = "treatment_plan_items"

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("treatment_plans.id", ondelete="CASCADE"), index=True)
    plan: Mapped[TreatmentPlan] = relationship(back_populates="items")
    treatment_id: Mapped[UUID] = mapped_column(ForeignKey("treatments.id", ondelete="RESTRICT"), index=True)
    tooth_code: Mapped[str | None] = mapped_column(String(2))
    treatment_code: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    currency: Mapped[str] = mapped_column(String(3), default="PYG")
