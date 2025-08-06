# pylint: disable=invalid-name
"""Switch CvrBallotContest PK from contest_id to contest_name

Revision ID: df756c355804
Revises: 3398d43e01c4
Create Date: 2025-08-06 20:36:36.055735+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "df756c355804"
down_revision = "3398d43e01c4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("cvr_ballot_contest_pkey", "cvr_ballot_contest", type_="primary")
    op.add_column(
        "cvr_ballot_contest",
        sa.Column("contest_name", sa.String(length=200), nullable=False),
    )
    op.drop_constraint(
        "cvr_ballot_contest_contest_id_fkey", "cvr_ballot_contest", type_="foreignkey"
    )
    op.drop_column("cvr_ballot_contest", "contest_id")
    op.create_primary_key(
        "cvr_ballot_contest_pkey",
        "cvr_ballot_contest",
        ["contest_name", "cvr_batch_id", "cvr_record_id"],
    )


def downgrade():  # pragma: no cover
    pass
