# pylint: disable=invalid-name
"""CvrBallotContest

Revision ID: 862a7ebc5a20
Revises: 7ca7a4b0bcc0
Create Date: 2025-07-29 19:44:34.229892+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "862a7ebc5a20"
down_revision = "7ca7a4b0bcc0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cvr_ballot_contest",
        sa.Column("cvr_batch_id", sa.String(length=200), nullable=False),
        sa.Column("cvr_record_id", sa.Integer(), nullable=False),
        sa.Column("contest_id", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["contest_id"],
            ["contest.id"],
            name=op.f("cvr_ballot_contest_contest_id_fkey"),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ["cvr_batch_id", "cvr_record_id"],
            ["cvr_ballot.batch_id", "cvr_ballot.record_id"],
            name=op.f("cvr_ballot_contest_cvr_batch_id_cvr_record_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "contest_id",
            "cvr_batch_id",
            "cvr_record_id",
            name=op.f("cvr_ballot_contest_pkey"),
        ),
    )


def downgrade():  # pragma: no cover
    pass
