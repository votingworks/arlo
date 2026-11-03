"""Batch.discrepancy_status and BatchDiscrepancyNote

Revision ID: 4c6d1dc93206
Revises: 1f3a9c2e7b5d
Create Date: 2026-10-30 17:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4c6d1dc93206"
down_revision = "1f3a9c2e7b5d"
branch_labels = None
depends_on = None


def upgrade():
    discrepancy_status_enum = sa.dialects.postgresql.ENUM(
        "NEEDS_REVIEW",
        "JURISDICTION_CONTACTED",
        "RE_TALLYING",
        "ACCEPTED",
        name="batchdiscrepancystatus",
    )
    discrepancy_status_enum.create(op.get_bind())
    op.add_column(
        "batch",
        sa.Column("discrepancy_status", discrepancy_status_enum, nullable=True),
    )
    op.create_table(
        "batch_discrepancy_note",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("batch_id", sa.String(length=200), nullable=False),
        sa.Column("user_email", sa.String(length=200), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batch.id"],
            name=op.f("batch_discrepancy_note_batch_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("batch_discrepancy_note_pkey")),
    )


def downgrade():  # pragma: no cover
    pass
