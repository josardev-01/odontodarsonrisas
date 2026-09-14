from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.modules.odontogram.schemas import valid_fdi
from app.modules.treatment_plans.models import PlanStatus


class PlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    clinical_notes: str | None = Field(default=None, max_length=4000)
    valid_until: date | None = None


class PlanItemCreate(BaseModel):
    treatment_id: UUID
    tooth_code: str | None = None
    quantity: int = Field(default=1, ge=1, le=100)
    unit_price: Decimal | None = Field(default=None, ge=0, decimal_places=0, max_digits=14)

    @field_validator("tooth_code")
    @classmethod
    def validate_optional_tooth(cls, value: str | None) -> str | None:
        if value is not None and not valid_fdi(value):
            raise ValueError("Invalid FDI tooth code")
        return value


class PlanItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    treatment_id: UUID
    tooth_code: str | None
    treatment_code: str
    description: str
    quantity: int
    unit_price: Decimal
    currency: str

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    created_by: UUID
    title: str
    clinical_notes: str | None
    status: PlanStatus
    valid_until: date | None
    accepted_at: datetime | None
    created_at: datetime
    items: list[PlanItemRead]

    @computed_field
    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal(0))


class PlanStatusChange(BaseModel):
    status: PlanStatus
