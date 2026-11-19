"""Index sampled_ballot_draw by contest

Revision ID: b3e7a5c1d9f2
Revises: 9c2d4f6a8b1e
Create Date: 2026-11-19 00:00:00.000000+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "b3e7a5c1d9f2"
down_revision = "9c2d4f6a8b1e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f("sampled_ballot_draw_contest_id_idx"),
        "sampled_ballot_draw",
        ["contest_id"],
        unique=False,
    )


def downgrade():  # pragma: no cover
    pass
