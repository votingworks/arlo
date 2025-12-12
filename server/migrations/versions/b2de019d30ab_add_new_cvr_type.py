"""Add new CVR type

Revision ID: b2de019d30ab
Revises: 4bf846480ccd
Create Date: 2025-12-11 13:14:56.177173+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2de019d30ab"
down_revision = "4bf846480ccd"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE cvrfiletype RENAME TO cvrfiletype_old")

    new_cvr_file_type_enum = sa.dialects.postgresql.ENUM(
        "DOMINION",
        "CLEARBALLOT",
        "ESS",
        "ESS_MD",
        "HART",
        "CLEARBALLOT_RCV",
        name="cvrfiletype",
    )
    new_cvr_file_type_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE jurisdiction ALTER COLUMN cvr_file_type TYPE cvrfiletype USING cvr_file_type::text::cvrfiletype"
    )

    op.execute("DROP TYPE cvrfiletype_old")


def downgrade():
    pass
