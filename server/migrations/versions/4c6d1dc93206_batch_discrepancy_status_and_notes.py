"""Batch.discrepancy_status and Batch.discrepancy_notes_by_contest_id

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
        "ACCEPTABLE",
        "JURISDICTION_CONTACTED",
        "RE_TALLYING",
        name="batchdiscrepancystatus",
    )
    discrepancy_status_enum.create(op.get_bind())
    op.add_column(
        "batch",
        sa.Column("discrepancy_status", discrepancy_status_enum, nullable=True),
    )
    op.add_column(
        "batch",
        sa.Column(
            "discrepancy_notes_by_contest_id",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade():  # pragma: no cover
    pass
