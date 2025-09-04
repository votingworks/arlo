"""BackgroundTask.worker_id

Revision ID: 6c256e8152f8
Revises: 34824a2d1ba8
Create Date: 2024-10-23 23:34:52.713596+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6c256e8152f8"
down_revision = "34824a2d1ba8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "background_task", sa.Column("worker_id", sa.String(length=200), nullable=True)
    )


def downgrade():  # pragma: no cover
    pass
