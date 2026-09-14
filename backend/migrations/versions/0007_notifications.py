"""Consent-aware WhatsApp and SMS notification outbox."""
from alembic import op
import sqlalchemy as sa

revision = "0007_notifications"
down_revision = "0006_billing_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_consents",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("channel", sa.Enum("WHATSAPP", "SMS", name="notificationchannel", native_enum=False, length=20), nullable=False),
        sa.Column("status", sa.Enum("GRANTED", "REVOKED", name="consentstatus", native_enum=False, length=20), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_location", sa.String(240), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("patient_id", "channel", name="uq_notification_consent_patient_channel"),
    )
    op.create_index("ix_notification_consents_patient_id", "notification_consents", ["patient_id"])
    op.create_index("ix_notification_consents_recorded_by", "notification_consents", ["recorded_by"])
    op.create_table(
        "notifications",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id", ondelete="RESTRICT")),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("channel", sa.Enum("WHATSAPP", "SMS", name="notificationchannel", native_enum=False, length=20), nullable=False),
        sa.Column("recipient", sa.String(16), nullable=False),
        sa.Column("template_key", sa.String(80)),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "SENT", "FAILED", "CANCELLED", name="notificationstatus", native_enum=False, length=20), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("provider_reference", sa.String(120)),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("patient_id", "appointment_id", "created_by", "channel", "status"):
        op.create_index(f"ix_notifications_{column}", "notifications", [column])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("notification_consents")
