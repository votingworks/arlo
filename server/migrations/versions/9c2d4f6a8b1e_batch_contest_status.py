"""BatchContestStatus

Revision ID: 9c2d4f6a8b1e
Revises: 7a1c3e9d2b4f
Create Date: 2026-11-06 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c2d4f6a8b1e"
down_revision = "7a1c3e9d2b4f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "batch_contest_status",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("batch_id", sa.String(length=200), nullable=False),
        sa.Column("contest_id", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NEEDS_REVIEW",
                "JURISDICTION_CONTACTED",
                "ACCEPTED",
                "MATCHES",
                "RE_TALLYING",
                name="batchdiscrepancystatus",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batch.id"],
            name=op.f("batch_contest_status_batch_id_fkey"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["contest_id"],
            ["contest.id"],
            name=op.f("batch_contest_status_contest_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "batch_id", "contest_id", name=op.f("batch_contest_status_pkey")
        ),
    )


def downgrade():  # pragma: no cover
    pass
