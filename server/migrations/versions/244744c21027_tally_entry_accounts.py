"""Tally entry accounts

Revision ID: 244744c21027
Revises: fed66f26125e
Create Date: 2022-10-12 23:37:55.383296+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "244744c21027"
down_revision = "fed66f26125e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tally_entry_user",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=200), nullable=False),
        sa.Column("member_1", sa.String(length=200), nullable=True),
        sa.Column(
            "member_1_affiliation",
            postgresql.ENUM(name="affiliation", create_type=False),
            nullable=True,
        ),
        sa.Column("member_2", sa.String(length=200), nullable=True),
        sa.Column(
            "member_2_affiliation",
            postgresql.ENUM(name="affiliation", create_type=False),
            nullable=True,
        ),
        sa.Column("login_code", sa.String(length=200), nullable=True),
        sa.Column("login_confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["jurisdiction_id"],
            ["jurisdiction.id"],
            name=op.f("tally_entry_user_jurisdiction_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("tally_entry_user_pkey")),
        sa.UniqueConstraint(
            "jurisdiction_id",
            "login_code",
            name=op.f("tally_entry_user_jurisdiction_id_login_code_key"),
        ),
    )
    op.add_column(
        "jurisdiction",
        sa.Column("tally_entry_passphrase", sa.String(length=200), nullable=True),
    )


def downgrade():  # pragma: no cover
    pass
