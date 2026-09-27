"""Link odontogram work, budget items and append-only evolution checklists."""

from alembic import op
import sqlalchemy as sa

revision = "0010_odontogram_evolution"
down_revision = "0009_clinical_history_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "odontogram_work_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), sa.ForeignKey("odontogram_events.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tooth_code", sa.String(2), nullable=False),
        sa.Column("surface", sa.Enum("WHOLE", "MESIAL", "DISTAL", "BUCCAL", "LINGUAL", "OCCLUSAL", "INCISAL", native_enum=False, length=20), nullable=False),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("treatment_code", sa.String(40), nullable=False),
        sa.Column("treatment_name", sa.String(200), nullable=False),
        sa.Column("current_plan_id", sa.Uuid(), sa.ForeignKey("treatment_plans.id", ondelete="RESTRICT")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("completed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("result_event_id", sa.Uuid(), sa.ForeignKey("odontogram_events.id", ondelete="RESTRICT")),
        sa.UniqueConstraint("source_event_id", name="uq_odontogram_work_source"),
    )
    op.create_index("ix_odontogram_work_items_patient_id", "odontogram_work_items", ["patient_id"])
    op.create_index("ix_odontogram_work_items_current_plan_id", "odontogram_work_items", ["current_plan_id"])
    op.add_column("treatment_plan_items", sa.Column("work_item_id", sa.Uuid(), sa.ForeignKey("odontogram_work_items.id", ondelete="RESTRICT")))
    op.create_index("ix_treatment_plan_items_work_item_id", "treatment_plan_items", ["work_item_id"])
    op.create_table(
        "evolution_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("work_item_id", sa.Uuid(), sa.ForeignKey("odontogram_work_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_item_id", sa.Uuid(), sa.ForeignKey("treatment_plan_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_evolution_entries_patient_id", "evolution_entries", ["patient_id"])
    op.create_index("ix_evolution_entries_work_item_id", "evolution_entries", ["work_item_id"])


def downgrade() -> None:
    connection = op.get_bind()
    if connection.scalar(sa.text("SELECT COUNT(*) FROM evolution_entries")) or connection.scalar(sa.text("SELECT COUNT(*) FROM odontogram_work_items")):
        raise RuntimeError("Restore the pre-migration backup before removing linked clinical work")
    op.drop_index("ix_evolution_entries_work_item_id", table_name="evolution_entries")
    op.drop_index("ix_evolution_entries_patient_id", table_name="evolution_entries")
    op.drop_table("evolution_entries")
    op.drop_index("ix_treatment_plan_items_work_item_id", table_name="treatment_plan_items")
    op.drop_column("treatment_plan_items", "work_item_id")
    op.drop_index("ix_odontogram_work_items_current_plan_id", table_name="odontogram_work_items")
    op.drop_index("ix_odontogram_work_items_patient_id", table_name="odontogram_work_items")
    op.drop_table("odontogram_work_items")
