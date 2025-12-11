"""Election.raire_assertions_pickle

Revision ID: 17dd7b178a3a
Revises: b2de019d30ab
Create Date: 2025-12-11 17:57:16.981448+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "17dd7b178a3a"
down_revision = "b2de019d30ab"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "election",
        sa.Column("raire_assertions_pickle", sa.LargeBinary(), nullable=True),
    )


def downgrade():
    pass
