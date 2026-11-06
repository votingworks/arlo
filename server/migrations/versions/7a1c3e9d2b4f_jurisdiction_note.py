"""JurisdictionNote

Revision ID: 7a1c3e9d2b4f
Revises: 1bb07ba303d2
Create Date: 2026-11-05 00:00:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a1c3e9d2b4f"
down_revision = "1bb07ba303d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jurisdiction_note",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=200), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["jurisdiction_id"],
            ["jurisdiction.id"],
            name=op.f("jurisdiction_note_jurisdiction_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("jurisdiction_note_pkey")),
    )


def downgrade():  # pragma: no cover
    pass
