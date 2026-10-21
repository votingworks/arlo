"""Name card style data math types after their base math type

Revision ID: 4258f5909ce2
Revises: 966d08450a18
Create Date: 2026-10-20 00:00:00.000000+00:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "4258f5909ce2"
down_revision = "966d08450a18"
branch_labels = None
depends_on = None


def upgrade():
    # Adding an enum value can't run inside a transaction before Postgres 12
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE auditmathtype ADD VALUE 'MACRO_CARD_STYLE_DATA'")
    op.execute(
        "ALTER TYPE auditmathtype"
        " RENAME VALUE 'CARD_STYLE_DATA' TO 'SUPERSIMPLE_CARD_STYLE_DATA'"
    )


def downgrade():  # pragma: no cover
    pass
