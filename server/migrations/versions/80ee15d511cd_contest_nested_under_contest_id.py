"""Contest.nested_under_contest_id

Revision ID: 80ee15d511cd
Revises: ea036eb33e57
Create Date: 2026-09-23 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "80ee15d511cd"
down_revision = "ea036eb33e57"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "contest",
        sa.Column("nested_under_contest_id", sa.String(length=200), nullable=True),
    )
    op.create_foreign_key(
        op.f("contest_nested_under_contest_id_fkey"),
        "contest",
        "contest",
        ["nested_under_contest_id"],
        ["id"],
        ondelete="set null",
        deferrable=True,
        initially="DEFERRED",
    )


def downgrade():  # pragma: no cover
    pass
