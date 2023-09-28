# pylint: disable=invalid-name
"""Jurisdiction.expected_manifest_num_ballots

Revision ID: fea3ed38fb6c
Revises: 848ffc831a04
Create Date: 2023-09-28 22:23:03.041933+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fea3ed38fb6c"
down_revision = "848ffc831a04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "jurisdiction",
        sa.Column("expected_manifest_num_ballots", sa.Integer(), nullable=True),
    )


def downgrade():
    pass  # pragma: no cover
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_column('jurisdiction', 'expected_manifest_num_ballots')
    # ### end Alembic commands ###
