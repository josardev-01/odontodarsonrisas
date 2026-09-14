import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.notifications.models import ConsentStatus, NotificationChannel, NotificationStatus

PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class ConsentCreate(BaseModel):
    channel: NotificationChannel
    granted_at: datetime
    evidence_location: str = Field(min_length=1, max_length=240)


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    channel: NotificationChannel
    status: ConsentStatus
    granted_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    evidence_location: str


class NotificationCreate(BaseModel):
    channel: NotificationChannel
    appointment_id: UUID | None = None
    recipient: str | None = Field(default=None, max_length=16)
    template_key: str | None = Field(default=None, min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9_.-]*$")
    message: str = Field(min_length=1, max_length=320)

    @field_validator("recipient")
    @classmethod
    def valid_recipient(cls, value: str | None) -> str | None:
        if value is not None and not PHONE_RE.fullmatch(value):
            raise ValueError("Phone must use E.164 format")
        return value

    @field_validator("message")
    @classmethod
    def minimal_message(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Message cannot be blank")
        return value


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    appointment_id: UUID | None
    channel: NotificationChannel
    recipient: str
    template_key: str | None
    message: str
    status: NotificationStatus
    processed_at: datetime | None
    cancelled_at: datetime | None
    provider_reference: str | None
    failure_code: str | None
    created_at: datetime


class NotificationResult(BaseModel):
    status: NotificationStatus
    provider_reference: str | None = Field(default=None, max_length=120)
    failure_code: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_result(self):
        if self.status not in {NotificationStatus.SENT, NotificationStatus.FAILED}:
            raise ValueError("Result status must be sent or failed")
        if self.status == NotificationStatus.FAILED and not self.failure_code:
            raise ValueError("failure_code is required for failed notifications")
        if self.status == NotificationStatus.SENT and self.failure_code:
            raise ValueError("failure_code is only valid for failed notifications")
        return self
