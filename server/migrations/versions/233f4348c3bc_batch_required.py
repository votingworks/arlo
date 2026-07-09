"""Batch.required

Revision ID: 233f4348c3bc
Revises: fda464935ab0
Create Date: 2026-07-07 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "233f4348c3bc"
down_revision = "fda464935ab0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch",
        sa.Column(
            "required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade():  # pragma: no cover
    pass
