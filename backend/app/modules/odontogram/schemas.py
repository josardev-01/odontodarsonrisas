from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.odontogram.models import DentalCondition, ToothSurface


def valid_fdi(code: str) -> bool:
    return len(code) == 2 and code.isdigit() and (
        (code[0] in "1234" and code[1] in "12345678")
        or (code[0] in "5678" and code[1] in "12345")
    )


class OdontogramEventCreate(BaseModel):
    tooth_code: str
    surface: ToothSurface
    condition: DentalCondition
    observed_at: datetime
    note: str | None = Field(default=None, max_length=2000)
    treatment_id: UUID | None = None

    @field_validator("tooth_code")
    @classmethod
    def validate_tooth(cls, value: str) -> str:
        if not valid_fdi(value):
            raise ValueError("Invalid FDI tooth code")
        return value

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone is required")
        return value


class OdontogramEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    recorded_by: UUID
    tooth_code: str
    surface: ToothSurface
    condition: DentalCondition
    observed_at: datetime
    note: str | None
    treatment_id: UUID | None
    created_at: datetime
