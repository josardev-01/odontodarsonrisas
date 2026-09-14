from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.database import Base
from app.platform.types import EntityMixin


class NotificationChannel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"


class ConsentStatus(StrEnum):
    GRANTED = "granted"
    REVOKED = "revoked"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationConsent(EntityMixin, Base):
    __tablename__ = "notification_consents"
    __table_args__ = (UniqueConstraint("patient_id", "channel", name="uq_notification_consent_patient_channel"),)

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, native_enum=False, length=20))
    status: Mapped[ConsentStatus] = mapped_column(Enum(ConsentStatus, native_enum=False, length=20), default=ConsentStatus.GRANTED)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    evidence_location: Mapped[str] = mapped_column(String(240))


class Notification(EntityMixin, Base):
    __tablename__ = "notifications"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    appointment_id: Mapped[UUID | None] = mapped_column(ForeignKey("appointments.id", ondelete="RESTRICT"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, native_enum=False, length=20), index=True)
    recipient: Mapped[str] = mapped_column(String(16))
    template_key: Mapped[str | None] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus, native_enum=False, length=20), default=NotificationStatus.PENDING, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_reference: Mapped[str | None] = mapped_column(String(120))
    failure_code: Mapped[str | None] = mapped_column(String(80))
