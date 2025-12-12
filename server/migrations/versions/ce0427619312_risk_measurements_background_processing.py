"""Risk measurements background processing

Revision ID: ce0427619312
Revises: 17dd7b178a3a
Create Date: 2025-12-12 03:10:10.179811+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ce0427619312"
down_revision = "17dd7b178a3a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "round",
        sa.Column(
            "calculate_risk_measurements_task_id", sa.String(length=200), nullable=True
        ),
    )
    op.create_foreign_key(
        op.f("round_calculate_risk_measurements_task_id_fkey"),
        "round",
        "background_task",
        ["calculate_risk_measurements_task_id"],
        ["id"],
        ondelete="set null",
    )


def downgrade():
    pass
