# pylint: disable=invalid-name
"""Add a sessions table as we move sessions to the backend.

Revision ID: 6a4dc1ef268c
Revises: 74c579ae8555
Create Date: 2023-01-27 17:38:29.934674+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a4dc1ef268c"
down_revision = "74c579ae8555"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "web_session",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("web_session_pkey")),
    )


def downgrade():  # pragma: no cover
    pass
