"""Standardized contests file

Revision ID: 5acbd2f95b9f
Revises: 7f86511c05e0
Create Date: 2020-09-30 22:38:19.350287+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5acbd2f95b9f"
down_revision = "7f86511c05e0"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("contest", "num_winners", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "contest", "total_ballots_cast", existing_type=sa.INTEGER(), nullable=True
    )
    op.alter_column(
        "contest", "votes_allowed", existing_type=sa.INTEGER(), nullable=True
    )
    op.add_column(
        "election", sa.Column("standardized_contests", sa.JSON(), nullable=True)
    )
    op.add_column(
        "election",
        sa.Column(
            "standardized_contests_file_id", sa.String(length=200), nullable=True
        ),
    )
    op.create_foreign_key(
        op.f("election_standardized_contests_file_id_fkey"),
        "election",
        "file",
        ["standardized_contests_file_id"],
        ["id"],
        ondelete="set null",
    )


def downgrade():  # pragma: no cover
    pass
