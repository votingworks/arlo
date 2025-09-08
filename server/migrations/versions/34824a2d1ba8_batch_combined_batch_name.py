"""Batch.combined_batch_name

Revision ID: 34824a2d1ba8
Revises: 8452f909a07e
Create Date: 2024-10-21 19:04:17.936262+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "34824a2d1ba8"
down_revision = "8452f909a07e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch", sa.Column("combined_batch_name", sa.String(length=200), nullable=True)
    )


def downgrade():  # pragma: no cover
    pass
