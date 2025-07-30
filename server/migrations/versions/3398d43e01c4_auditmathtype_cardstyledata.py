# pylint: disable=invalid-name
"""AuditMathType.CARDSTYLEDATA

Revision ID: 3398d43e01c4
Revises: 862a7ebc5a20
Create Date: 2025-07-30 23:18:46.975812+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "3398d43e01c4"
down_revision = "862a7ebc5a20"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE auditmathtype ADD VALUE IF NOT EXISTS 'CARDSTYLEDATA'")


def downgrade():  # pragma: no cover
    pass
