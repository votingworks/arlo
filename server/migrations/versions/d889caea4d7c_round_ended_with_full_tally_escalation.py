"""Round.ended_with_full_tally_escalation

Revision ID: d889caea4d7c
Revises: 4258f5909ce2
Create Date: 2026-10-21 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d889caea4d7c"
down_revision = "4258f5909ce2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "round",
        sa.Column("ended_with_full_tally_escalation", sa.Boolean(), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
