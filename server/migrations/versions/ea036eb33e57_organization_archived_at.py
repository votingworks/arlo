"""Organization.archived_at

Revision ID: ea036eb33e57
Revises: 233f4348c3bc
Create Date: 2026-08-25 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ea036eb33e57"
down_revision = "233f4348c3bc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organization", sa.Column("archived_at", sa.DateTime(), nullable=True)
    )


def downgrade():  # pragma: no cover
    pass
