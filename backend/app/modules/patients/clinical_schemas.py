from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.patients.models import ClinicalEntryType, ConsentStatus


class ClinicalProfileWrite(BaseModel):
    blood_type: str | None = Field(default=None, max_length=10)
    allergies: list[str] = Field(default_factory=list, max_length=50)
    medications: list[str] = Field(default_factory=list, max_length=50)
    medical_conditions: list[str] = Field(default_factory=list, max_length=50)
    observations: str | None = Field(default=None, max_length=4000)

    @field_validator("allergies", "medications", "medical_conditions")
    @classmethod
    def clean_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if any(len(value) > 160 for value in cleaned):
            raise ValueError("Each item must have at most 160 characters")
        return list(dict.fromkeys(cleaned))


class ClinicalProfileRead(ClinicalProfileWrite):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    updated_at: datetime
    updated_by: UUID


class ClinicalEntryBase(BaseModel):
    entry_type: ClinicalEntryType
    occurred_at: datetime
    summary: str = Field(min_length=1, max_length=240)
    notes: str = Field(min_length=1, max_length=12000)


class ClinicalEntryCreate(ClinicalEntryBase):

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone is required")
        return value


class ClinicalEntryRead(ClinicalEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    author_id: UUID
    created_at: datetime


class ConsentBase(BaseModel):
    consent_type: str = Field(min_length=1, max_length=80)
    document_version: str = Field(min_length=1, max_length=40)
    purpose: str = Field(min_length=1, max_length=240)
    signed_at: datetime
    signer_name: str = Field(min_length=1, max_length=160)
    signer_relationship: str | None = Field(default=None, max_length=80)
    evidence_location: str = Field(min_length=1, max_length=300)


class ConsentCreate(ConsentBase):

    @field_validator("signed_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone is required")
        return value


class ConsentRead(ConsentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    recorded_by: UUID
    status: ConsentStatus
    revoked_at: datetime | None
    created_at: datetime
