# pylint: disable=invalid-name
"""Batch.last_edited_by

Revision ID: 9e8dbf652ed7
Revises: 244744c21027
Create Date: 2022-11-04 17:03:46.183670+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9e8dbf652ed7"
down_revision = "244744c21027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch",
        sa.Column("last_edited_by_user_type", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "batch",
        sa.Column("last_edited_by_user_key", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "batch",
        sa.Column(
            "last_edited_by_support_user_email", sa.String(length=200), nullable=True
        ),
    )


def downgrade():  # pragma: no cover
    pass
