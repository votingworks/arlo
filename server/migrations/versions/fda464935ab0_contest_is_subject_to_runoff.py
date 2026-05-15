"""contest_is_subject_to_runoff

Revision ID: fda464935ab0
Revises: 4b1bf0241301
Create Date: 2026-05-15 20:25:22.615362+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fda464935ab0"
down_revision = "4b1bf0241301"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "contest",
        sa.Column(
            "is_subject_to_runoff",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade():  # pragma: no cover
    pass
