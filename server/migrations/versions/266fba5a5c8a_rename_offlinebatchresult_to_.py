# pylint: disable=invalid-name
"""Rename OfflineBatchResult to FullHandTallyBatchResult

Revision ID: 266fba5a5c8a
Revises: 30f47ec7308c
Create Date: 2021-11-04 17:29:16.156954+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "266fba5a5c8a"
down_revision = "30f47ec7308c"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("offline_batch_result", "full_hand_tally_batch_result")
    op.drop_constraint("offline_batch_result_pkey", "full_hand_tally_batch_result")
    op.drop_constraint(
        "offline_batch_result_jurisdiction_id_fkey", "full_hand_tally_batch_result"
    )
    op.drop_constraint(
        "offline_batch_result_contest_choice_id_fkey", "full_hand_tally_batch_result"
    )
    op.create_foreign_key(
        "full_hand_tally_batch_result_contest_choice_id_fkey",
        "full_hand_tally_batch_result",
        "contest_choice",
        ["contest_choice_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        "full_hand_tally_batch_result_jurisdiction_id_fkey",
        "full_hand_tally_batch_result",
        "jurisdiction",
        ["jurisdiction_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_primary_key(
        "full_hand_tally_batch_result_pkey",
        "full_hand_tally_batch_result",
        [
            "jurisdiction_id",
            "batch_name",
            "contest_choice_id",
        ],
    )

    op.alter_column(
        "jurisdiction",
        "finalized_offline_batch_results_at",
        new_column_name="finalized_full_hand_tally_results_at",
    )


def downgrade():  # pragma: no cover
    pass
