from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base
from app.platform.types import EntityMixin


class ToothSurface(StrEnum):
    WHOLE = "whole"
    MESIAL = "mesial"
    DISTAL = "distal"
    BUCCAL = "buccal"
    LINGUAL = "lingual"
    OCCLUSAL = "occlusal"
    INCISAL = "incisal"


class DentalCondition(StrEnum):
    HEALTHY = "healthy"
    CARIES = "caries"
    MISSING = "missing"
    RESTORATION = "restoration"
    CROWN = "crown"
    IMPLANT = "implant"
    ROOT_CANAL = "root_canal"
    EXTRACTION_INDICATED = "extraction_indicated"


class OdontogramEvent(EntityMixin, Base):
    __tablename__ = "odontogram_events"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    tooth_code: Mapped[str] = mapped_column(String(2), index=True)
    surface: Mapped[ToothSurface] = mapped_column(Enum(ToothSurface, native_enum=False, length=20), index=True)
    condition: Mapped[DentalCondition] = mapped_column(Enum(DentalCondition, native_enum=False, length=30), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    note: Mapped[str | None] = mapped_column(Text)
    treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id", ondelete="SET NULL"), index=True)


class OdontogramWorkItem(EntityMixin, Base):
    __tablename__ = "odontogram_work_items"
    __table_args__ = (UniqueConstraint("source_event_id", name="uq_odontogram_work_source"),)

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    source_event_id: Mapped[UUID] = mapped_column(ForeignKey("odontogram_events.id", ondelete="RESTRICT"))
    tooth_code: Mapped[str] = mapped_column(String(2))
    surface: Mapped[ToothSurface] = mapped_column(Enum(ToothSurface, native_enum=False, length=20))
    treatment_id: Mapped[UUID] = mapped_column(ForeignKey("treatments.id", ondelete="RESTRICT"))
    treatment_code: Mapped[str] = mapped_column(String(40))
    treatment_name: Mapped[str] = mapped_column(String(200))
    current_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatment_plans.id", ondelete="RESTRICT"), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    result_event_id: Mapped[UUID | None] = mapped_column(ForeignKey("odontogram_events.id", ondelete="RESTRICT"))
