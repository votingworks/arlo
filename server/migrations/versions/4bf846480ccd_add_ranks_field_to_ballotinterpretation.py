"""Add ranks field to BallotInterpretation

Revision ID: 4bf846480ccd
Revises: 4b1bf0241301
Create Date: 2025-12-11 11:27:59.349829+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4bf846480ccd"
down_revision = "4b1bf0241301"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ballot_interpretation", sa.Column("ranks", sa.JSON(), nullable=True))
    op.drop_column("ballot_interpretation", "selected_choices")


def downgrade():
    pass
