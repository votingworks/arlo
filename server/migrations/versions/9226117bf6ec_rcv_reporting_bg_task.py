"""RCV reporting bg task

Revision ID: 9226117bf6ec
Revises: 9638492137c0
Create Date: 2025-12-12 05:43:03.299355+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9226117bf6ec"
down_revision = "9638492137c0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "round",
        sa.Column("generate_report_task_id", sa.String(length=200), nullable=True),
    )
    op.create_foreign_key(
        op.f("round_generate_report_task_id_fkey"),
        "round",
        "background_task",
        ["generate_report_task_id"],
        ["id"],
        ondelete="set null",
    )


def downgrade():
    pass
