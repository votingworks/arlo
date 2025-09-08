"""Fix delete cascades

Revision ID: 593823da406d
Revises: f63ba2f2da22
Create Date: 2022-03-08 01:17:04.936981+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "593823da406d"
down_revision = "dd3f3330aee2"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "ballot_interpretation_contest_choice_contest_choice_id__60bf",
        "ballot_interpretation_contest_choice",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ballot_interpretation_contest_choice_ballot_id_contest_id_fkey",
        "ballot_interpretation_contest_choice",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("ballot_interpretation_contest_choice_contest_choice_id_contest_id_fkey"),
        "ballot_interpretation_contest_choice",
        "contest_choice",
        ["contest_choice_id", "contest_id"],
        ["id", "contest_id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        op.f("ballot_interpretation_contest_choice_ballot_id_contest_id_fkey"),
        "ballot_interpretation_contest_choice",
        "ballot_interpretation",
        ["ballot_id", "contest_id"],
        ["ballot_id", "contest_id"],
        ondelete="cascade",
    )


def downgrade():  # pragma: no cover
    pass
