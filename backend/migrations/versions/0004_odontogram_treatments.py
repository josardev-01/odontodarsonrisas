"""Treatment catalog and append-only FDI odontogram events."""
from alembic import op
import sqlalchemy as sa

revision = "0004_odontogram_treatments"
down_revision = "0003_patient_clinical_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treatments",
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("default_price", sa.Numeric(14, 0), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_treatments_code", "treatments", ["code"], unique=True)
    op.create_index("ix_treatments_name", "treatments", ["name"])
    op.create_index("ix_treatments_category", "treatments", ["category"])

    op.create_table(
        "odontogram_events",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tooth_code", sa.String(2), nullable=False),
        sa.Column("surface", sa.Enum("WHOLE", "MESIAL", "DISTAL", "BUCCAL", "LINGUAL", "OCCLUSAL", "INCISAL", name="toothsurface", native_enum=False, length=20), nullable=False),
        sa.Column("condition", sa.Enum("HEALTHY", "CARIES", "MISSING", "RESTORATION", "CROWN", "IMPLANT", "ROOT_CANAL", "EXTRACTION_INDICATED", name="dentalcondition", native_enum=False, length=30), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL")),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("patient_id", "recorded_by", "tooth_code", "surface", "condition", "observed_at", "treatment_id"):
        op.create_index(f"ix_odontogram_events_{column}", "odontogram_events", [column])


def downgrade() -> None:
    op.drop_table("odontogram_events")
    op.drop_table("treatments")
