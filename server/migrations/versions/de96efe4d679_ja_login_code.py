# pylint: disable=invalid-name
"""JA login code

Revision ID: de96efe4d679
Revises: 8ab39ac619ed
Create Date: 2021-07-26 23:24:40.589600+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "de96efe4d679"
down_revision = "8ab39ac619ed"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("login_code", sa.String(length=200), nullable=True))
    op.add_column(
        "user", sa.Column("login_code_requested_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "user",
        sa.Column("login_code_attempts", sa.Integer(), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
