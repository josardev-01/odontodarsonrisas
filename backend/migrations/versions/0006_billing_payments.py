"""Internal invoices and immutable payment records."""
from alembic import op
import sqlalchemy as sa

revision = "0006_billing_payments"
down_revision = "0005_treatment_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("treatment_plan_id", sa.Uuid(), sa.ForeignKey("treatment_plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number", sa.String(32), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(14, 0), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("status", sa.Enum("ISSUED", "PARTIALLY_PAID", "PAID", "CANCELLED", name="invoicestatus", native_enum=False, length=30), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("treatment_plan_id"),
        sa.UniqueConstraint("number"),
    )
    for column in ("patient_id", "treatment_plan_id", "created_by", "number", "status"):
        op.create_index(f"ix_invoices_{column}", "invoices", [column])
    op.create_table(
        "payments",
        sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 0), nullable=False),
        sa.Column("method", sa.Enum("CASH", "CARD", "TRANSFER", "OTHER", name="paymentmethod", native_enum=False, length=20), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.String(120)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_recorded_by", "payments", ["recorded_by"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("invoices")
