# pylint: disable=invalid-name
"""Jurisdiction.contest_choice_name_standardizations

Revision ID: 8452f909a07e
Revises: cb8de251c1a5
Create Date: 2024-06-19 20:40:42.730393+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8452f909a07e"
down_revision = "cb8de251c1a5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "jurisdiction",
        sa.Column("contest_choice_name_standardizations", sa.JSON(), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
