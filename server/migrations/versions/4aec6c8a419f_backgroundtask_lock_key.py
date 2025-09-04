"""BackgroundTask.lock_key

Revision ID: 4aec6c8a419f
Revises: 6c256e8152f8
Create Date: 2024-10-28 23:56:45.256277+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4aec6c8a419f"
down_revision = "6c256e8152f8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "background_task", sa.Column("lock_key", sa.String(length=200), nullable=True)
    )


def downgrade():  # pragma: no cover
    pass
