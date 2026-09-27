"""Archive signed physical clinical history scans without replacing earlier versions."""

from alembic import op
import sqlalchemy as sa

revision = "0009_clinical_history_documents"
down_revision = "0008_consent_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_history_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attachment_filename", sa.String(180), nullable=False),
        sa.Column("attachment_content_type", sa.String(40), nullable=False),
        sa.Column("attachment_size", sa.Integer(), nullable=False),
        sa.Column("attachment_sha256", sa.String(64), nullable=False),
        sa.Column("attachment_data", sa.LargeBinary(), nullable=False),
    )
    op.create_index("ix_clinical_history_documents_patient_id", "clinical_history_documents", ["patient_id"])


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT COUNT(*) FROM clinical_history_documents")):
        raise RuntimeError("Restore the pre-migration backup before removing clinical history documents")
    op.drop_index("ix_clinical_history_documents_patient_id", table_name="clinical_history_documents")
    op.drop_table("clinical_history_documents")
