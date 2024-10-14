# pylint: disable=invalid-name
"""CvrFileType.ESS

Revision ID: dd3f3330aee2
Revises: bc97ac0e8267
Create Date: 2021-11-17 00:00:45.284416+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dd3f3330aee2"
down_revision = "bc97ac0e8267"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE cvrfiletype RENAME TO cvrfiletype_old")

    new_cvr_file_type_enum = sa.dialects.postgresql.ENUM(
        "DOMINION",
        "CLEARBALLOT",
        "ESS",
        name="cvrfiletype",
    )
    new_cvr_file_type_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE jurisdiction ALTER COLUMN cvr_file_type TYPE cvrfiletype USING cvr_file_type::text::cvrfiletype"
    )

    op.execute("DROP TYPE cvrfiletype_old")


def downgrade():  # pragma: no cover
    pass
