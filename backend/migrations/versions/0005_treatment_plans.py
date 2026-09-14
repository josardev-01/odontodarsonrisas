"""Treatment plans with immutable price snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0005_treatment_plans"
down_revision = "0004_odontogram_treatments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "treatment_plans",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("clinical_notes", sa.Text()),
        sa.Column("status", sa.Enum("DRAFT", "PROPOSED", "ACCEPTED", "REJECTED", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="planstatus", native_enum=False, length=30), nullable=False),
        sa.Column("valid_until", sa.Date()),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("patient_id", "created_by", "status"):
        op.create_index(f"ix_treatment_plans_{column}", "treatment_plans", [column])
    op.create_table(
        "treatment_plan_items",
        sa.Column("plan_id", sa.Uuid(), sa.ForeignKey("treatment_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tooth_code", sa.String(2)),
        sa.Column("treatment_code", sa.String(40), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 0), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_treatment_plan_items_plan_id", "treatment_plan_items", ["plan_id"])
    op.create_index("ix_treatment_plan_items_treatment_id", "treatment_plan_items", ["treatment_id"])


def downgrade() -> None:
    op.drop_table("treatment_plan_items")
    op.drop_table("treatment_plans")
