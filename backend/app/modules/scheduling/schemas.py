from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.scheduling.models import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: UUID
    professional_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def valid_window(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Appointment timestamps must include a timezone")
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        return self


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    professional_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str | None
    status: AppointmentStatus
    created_at: datetime

    @field_validator("starts_at", "ends_at", mode="before")
    @classmethod
    def serialize_as_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class AppointmentReschedule(BaseModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def valid_window(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Appointment timestamps must include a timezone")
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be before ends_at")
        return self


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
