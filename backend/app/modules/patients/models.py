from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.database import Base
from app.platform.types import EntityMixin


class Patient(EntityMixin, Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("document_type", "document_number", name="uq_patient_document"),
    )

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    document_type: Mapped[str] = mapped_column(String(30))
    document_number: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(254))
    address: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(100))
    occupation: Mapped[str | None] = mapped_column(String(120))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(160))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(40))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ClinicalProfile(EntityMixin, Base):
    __tablename__ = "clinical_profiles"
    __table_args__ = (UniqueConstraint("patient_id", name="uq_clinical_profile_patient"),)

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    blood_type: Mapped[str | None] = mapped_column(String(10))
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list)
    medications: Mapped[list[str]] = mapped_column(JSON, default=list)
    medical_conditions: Mapped[list[str]] = mapped_column(JSON, default=list)
    observations: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class ClinicalEntryType(StrEnum):
    CONSULTATION = "consultation"
    EVOLUTION = "evolution"
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"


class ClinicalEntry(EntityMixin, Base):
    __tablename__ = "clinical_entries"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    entry_type: Mapped[ClinicalEntryType] = mapped_column(Enum(ClinicalEntryType, native_enum=False, length=30), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    summary: Mapped[str] = mapped_column(String(240))
    notes: Mapped[str] = mapped_column(Text)


class ConsentStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class ConsentRecord(EntityMixin, Base):
    __tablename__ = "consent_records"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    consent_type: Mapped[str] = mapped_column(String(80), index=True)
    document_version: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(240))
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    signer_name: Mapped[str] = mapped_column(String(160))
    signer_relationship: Mapped[str | None] = mapped_column(String(80))
    evidence_location: Mapped[str] = mapped_column(String(300))
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    status: Mapped[ConsentStatus] = mapped_column(Enum(ConsentStatus, native_enum=False, length=20), default=ConsentStatus.ACTIVE)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
