# pylint: disable=invalid-name
"""CvrFileType.HART

Revision ID: 496ee3db6da8
Revises: 593823da406d
Create Date: 2022-04-19 17:30:53.895058+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "496ee3db6da8"
down_revision = "593823da406d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE cvrfiletype RENAME TO cvrfiletype_old")

    new_cvr_file_type_enum = sa.dialects.postgresql.ENUM(
        "DOMINION",
        "CLEARBALLOT",
        "ESS",
        "HART",
        name="cvrfiletype",
    )
    new_cvr_file_type_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE jurisdiction ALTER COLUMN cvr_file_type TYPE cvrfiletype USING cvr_file_type::text::cvrfiletype"
    )

    op.execute("DROP TYPE cvrfiletype_old")


def downgrade():  # pragma: no cover
    pass
