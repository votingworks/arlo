"""CVRs

Revision ID: 7f86511c05e0
Revises: 3edc260ab0b1
Create Date: 2020-09-30 01:42:33.566537+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f86511c05e0"
down_revision = "3edc260ab0b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cvr_ballot",
        sa.Column("batch_id", sa.String(length=200), nullable=False),
        sa.Column("ballot_position", sa.Integer(), nullable=False),
        sa.Column("imprinted_id", sa.String(length=200), nullable=False),
        sa.Column("interpretations", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batch.id"],
            name=op.f("cvr_ballot_batch_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "batch_id", "ballot_position", name=op.f("cvr_ballot_pkey")
        ),
    )
    op.add_column(
        "jurisdiction", sa.Column("cvr_contests_metadata", sa.JSON(), nullable=True)
    )
    op.add_column(
        "jurisdiction", sa.Column("cvr_file_id", sa.String(length=200), nullable=True)
    )
    op.create_foreign_key(
        op.f("jurisdiction_cvr_file_id_fkey"),
        "jurisdiction",
        "file",
        ["cvr_file_id"],
        ["id"],
        ondelete="set null",
    )


def downgrade():  # pragma: no cover
    pass
