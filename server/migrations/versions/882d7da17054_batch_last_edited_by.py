# pylint: disable=invalid-name
"""Batch.last_edited_by

Revision ID: 882d7da17054
Revises: 244744c21027
Create Date: 2022-11-10 23:40:20.037437+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "882d7da17054"
down_revision = "244744c21027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch",
        sa.Column(
            "last_edited_by_support_user_email", sa.String(length=200), nullable=True
        ),
    )
    op.add_column(
        "batch",
        sa.Column(
            "last_edited_by_jurisdiction_admin_email",
            sa.String(length=200),
            nullable=True,
        ),
    )
    op.add_column(
        "batch",
        sa.Column(
            "last_edited_by_tally_entry_user_id", sa.String(length=200), nullable=True
        ),
    )
    op.create_foreign_key(
        op.f("batch_last_edited_by_tally_entry_user_id_fkey"),
        "batch",
        "tally_entry_user",
        ["last_edited_by_tally_entry_user_id"],
        ["id"],
        ondelete="set null",
    )

    # Added manually since Alembic auto-generation doesn't yet support adding check constraints:
    # https://github.com/sqlalchemy/alembic/issues/508
    op.create_check_constraint(
        "only_one_of_last_edited_by_fields_is_specified_check",
        "batch",
        "(cast(last_edited_by_support_user_email is not null as int) +"
        " cast(last_edited_by_jurisdiction_admin_email is not null as int) +"
        " cast(last_edited_by_tally_entry_user_id is not null as int)) <= 1",
    )


def downgrade():  # pragma: no cover
    pass
