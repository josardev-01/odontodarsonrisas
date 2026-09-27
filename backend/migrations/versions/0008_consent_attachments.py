"""Store signed consent scans in the database and retain notification grant history."""

from alembic import op
import sqlalchemy as sa

revision = "0008_consent_attachments"
down_revision = "0007_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_notification_consent_patient_channel", "notification_consents", type_="unique")
    op.create_index(
        "ix_notification_consents_patient_channel_created",
        "notification_consents",
        ["patient_id", "channel", "created_at"],
    )
    for table, length in (("consent_records", 300), ("notification_consents", 240)):
        op.alter_column(table, "evidence_location", existing_type=sa.String(length), nullable=True)
        op.add_column(table, sa.Column("attachment_filename", sa.String(180)))
        op.add_column(table, sa.Column("attachment_content_type", sa.String(40)))
        op.add_column(table, sa.Column("attachment_size", sa.Integer()))
        op.add_column(table, sa.Column("attachment_sha256", sa.String(64)))
        op.add_column(table, sa.Column("attachment_data", sa.LargeBinary()))


def downgrade() -> None:
    connection = op.get_bind()
    for table in ("consent_records", "notification_consents"):
        attached = connection.scalar(sa.text(f"SELECT COUNT(*) FROM {table} WHERE attachment_data IS NOT NULL"))
        if attached:
            raise RuntimeError("Restore the pre-migration backup before removing signed documents")
    versions = connection.scalar(sa.text(
        "SELECT COUNT(*) FROM (SELECT patient_id, channel FROM notification_consents "
        "GROUP BY patient_id, channel HAVING COUNT(*) > 1) AS multiple_versions"
    ))
    if versions:
        raise RuntimeError("Restore the pre-migration backup before removing notification authorization history")
    for table, length in (("notification_consents", 240), ("consent_records", 300)):
        op.drop_column(table, "attachment_data")
        op.drop_column(table, "attachment_sha256")
        op.drop_column(table, "attachment_size")
        op.drop_column(table, "attachment_content_type")
        op.drop_column(table, "attachment_filename")
        # Legacy clients may have stored only a scan. Preserve a readable marker.
        op.execute(sa.text(f"UPDATE {table} SET evidence_location = 'Adjunto digital retirado' WHERE evidence_location IS NULL"))
        op.alter_column(table, "evidence_location", existing_type=sa.String(length), nullable=False)
    op.drop_index("ix_notification_consents_patient_channel_created", table_name="notification_consents")
    op.create_unique_constraint("uq_notification_consent_patient_channel", "notification_consents", ["patient_id", "channel"])
