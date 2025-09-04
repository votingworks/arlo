"""SampledBatchDraw.contest_id

Revision ID: c012fa6b13a9
Revises: 83bc53b14021
Create Date: 2024-02-09 15:38:22.522331+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c012fa6b13a9"
down_revision = "83bc53b14021"
branch_labels = None
depends_on = None


def upgrade():
    # Add SampledBatchDraw.contest_id
    op.add_column("sampled_batch_draw", sa.Column("contest_id", sa.String(length=200)))
    op.create_foreign_key(
        op.f("sampled_batch_draw_contest_id_fkey"),
        "sampled_batch_draw",
        "contest",
        ["contest_id"],
        ["id"],
        ondelete="cascade",
    )

    # Populate the field for existing SampledBatchDraws
    op.execute(
        """
        UPDATE sampled_batch_draw
        SET contest_id = contest.id
        FROM contest
        JOIN election ON election.id = contest.election_id
        JOIN round ON election.id = round.election_id
        WHERE round.id = sampled_batch_draw.round_id
        """
    )

    # Make the field required
    op.alter_column("sampled_batch_draw", "contest_id", nullable=False)

    # Update the SampledBatchDraw primary key
    op.drop_constraint(op.f("sampled_batch_draw_pkey"), "sampled_batch_draw")
    op.create_primary_key(
        op.f("sampled_batch_draw_pkey"),
        "sampled_batch_draw",
        ["batch_id", "round_id", "contest_id", "ticket_number"],
    )


def downgrade():  # pragma: no cover
    pass
