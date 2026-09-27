"""Store a single control check while preserving prior checklist entries."""

from alembic import op
import sqlalchemy as sa

revision = "0011_evolution_control"
down_revision = "0010_odontogram_evolution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evolution_entries", sa.Column("control_completed", sa.Boolean()))


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT COUNT(*) FROM evolution_entries WHERE control_completed IS NOT NULL")):
        raise RuntimeError("Restore the pre-migration backup before removing control records")
    op.drop_column("evolution_entries", "control_completed")
