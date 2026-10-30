"""ActivityLogRecord.posted_to_slack_channels

Revision ID: 1bb07ba303d2
Revises: d889caea4d7c
Create Date: 2026-10-29 23:07:56.036733+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "1bb07ba303d2"
down_revision = "d889caea4d7c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "activity_log_record",
        sa.Column(
            "posted_to_slack_channels",
            postgresql.ARRAY(sa.String(length=200)),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade():  # pragma: no cover
    pass
