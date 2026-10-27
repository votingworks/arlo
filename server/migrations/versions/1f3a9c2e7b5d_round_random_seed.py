"""Round.random_seed

Revision ID: 1f3a9c2e7b5d
Revises: d889caea4d7c
Create Date: 2026-10-27 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1f3a9c2e7b5d"
down_revision = "d889caea4d7c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "round",
        sa.Column("random_seed", sa.String(length=100), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
