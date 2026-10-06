"""Batch.num_ballots_by_contest_id

Revision ID: 966d08450a18
Revises: 80ee15d511cd
Create Date: 2026-10-06 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "966d08450a18"
down_revision = "80ee15d511cd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch",
        sa.Column("num_ballots_by_contest_id", sa.JSON(), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
