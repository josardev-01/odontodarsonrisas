"""Detailed patient profile, append-only clinical history and consent evidence."""
from alembic import op
import sqlalchemy as sa

revision = "0003_patient_clinical_history"
down_revision = "0002_staff_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, length in (
        ("address", 300),
        ("city", 100),
        ("occupation", 120),
        ("emergency_contact_name", 160),
        ("emergency_contact_phone", 40),
    ):
        op.add_column("patients", sa.Column(name, sa.String(length), nullable=True))

    op.create_table(
        "clinical_profiles",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("blood_type", sa.String(10)),
        sa.Column("allergies", sa.JSON(), nullable=False),
        sa.Column("medications", sa.JSON(), nullable=False),
        sa.Column("medical_conditions", sa.JSON(), nullable=False),
        sa.Column("observations", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("patient_id", name="uq_clinical_profile_patient"),
    )
    op.create_index("ix_clinical_profiles_patient_id", "clinical_profiles", ["patient_id"])

    op.create_table(
        "clinical_entries",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("entry_type", sa.Enum("CONSULTATION", "EVOLUTION", "DIAGNOSIS", "PROCEDURE", name="clinicalentrytype", native_enum=False, length=30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.String(240), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("patient_id", "author_id", "entry_type", "occurred_at"):
        op.create_index(f"ix_clinical_entries_{column}", "clinical_entries", [column])

    op.create_table(
        "consent_records",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("consent_type", sa.String(80), nullable=False),
        sa.Column("document_version", sa.String(40), nullable=False),
        sa.Column("purpose", sa.String(240), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signer_name", sa.String(160), nullable=False),
        sa.Column("signer_relationship", sa.String(80)),
        sa.Column("evidence_location", sa.String(300), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "REVOKED", name="consentstatus", native_enum=False, length=20), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("patient_id", "consent_type", "signed_at"):
        op.create_index(f"ix_consent_records_{column}", "consent_records", [column])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("clinical_entries")
    op.drop_table("clinical_profiles")
    for name in ("emergency_contact_phone", "emergency_contact_name", "occupation", "city", "address"):
        op.drop_column("patients", name)
