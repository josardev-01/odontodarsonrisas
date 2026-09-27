from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base
from app.platform.types import EntityMixin


class EvolutionEntry(EntityMixin, Base):
    __tablename__ = "evolution_entries"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    work_item_id: Mapped[UUID] = mapped_column(ForeignKey("odontogram_work_items.id", ondelete="RESTRICT"), index=True)
    plan_item_id: Mapped[UUID] = mapped_column(ForeignKey("treatment_plan_items.id", ondelete="RESTRICT"))
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    answers: Mapped[list[dict]] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
