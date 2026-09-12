"""Initial vertical slice schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("patients", sa.Column("first_name", sa.String(100), nullable=False), sa.Column("last_name", sa.String(100), nullable=False), sa.Column("document_type", sa.String(30), nullable=False), sa.Column("document_number", sa.String(80), nullable=False), sa.Column("birth_date", sa.Date()), sa.Column("phone", sa.String(40)), sa.Column("email", sa.String(254)), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("document_type", "document_number", name="uq_patient_document"))
    op.create_index("ix_patients_last_name", "patients", ["last_name"])
    op.create_table("professionals", sa.Column("display_name", sa.String(160), nullable=False), sa.Column("specialty", sa.String(120), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    status_enum = sa.Enum("SCHEDULED", "CANCELLED", "COMPLETED", name="appointmentstatus")
    op.create_table("appointments", sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False), sa.Column("professional_id", sa.Uuid(), sa.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False), sa.Column("reason", sa.String(300)), sa.Column("status", status_enum, nullable=False), sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_professional_id", "appointments", ["professional_id"])
    op.create_index("ix_appointments_professional_window", "appointments", ["professional_id", "starts_at", "ends_at"])
    op.create_table("audit_events", sa.Column("actor_id", sa.String(120), nullable=False), sa.Column("action", sa.String(100), nullable=False), sa.Column("resource_type", sa.String(80), nullable=False), sa.Column("resource_id", sa.Uuid()), sa.Column("outcome", sa.String(40), nullable=False), sa.Column("detail", sa.Text()), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for column in ("actor_id", "action", "resource_type", "occurred_at"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute(
            "ALTER TABLE appointments ADD CONSTRAINT ex_appointments_professional_window "
            "EXCLUDE USING gist (professional_id WITH =, "
            "tstzrange(starts_at, ends_at, '[)') WITH &&) "
            "WHERE (status = 'SCHEDULED')"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS ex_appointments_professional_window")
    op.drop_table("audit_events")
    op.drop_table("appointments")
    op.drop_table("professionals")
    op.drop_table("patients")
    sa.Enum(name="appointmentstatus").drop(op.get_bind(), checkfirst=True)
