# pylint: disable=invalid-name
"""Contest.pending_ballots

Revision ID: 7ca7a4b0bcc0
Revises: 4aec6c8a419f
Create Date: 2024-11-05 21:12:31.908179+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7ca7a4b0bcc0"
down_revision = "4aec6c8a419f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("contest", sa.Column("pending_ballots", sa.Integer(), nullable=True))


def downgrade():  # pragma: no cover
    pass
