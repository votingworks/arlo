# pylint: disable=invalid-name
"""AuditMathType.RAIRE

Revision ID: f63ba2f2da22
Revises: dd3f3330aee2
Create Date: 2022-03-02 00:29:49.856025+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f63ba2f2da22"
down_revision = "dd3f3330aee2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE auditmathtype RENAME TO auditmathtype_old")

    new_audit_math_type_enum = sa.dialects.postgresql.ENUM(
        "BRAVO",
        "MINERVA",
        "SUPERSIMPLE",
        "MACRO",
        "SUITE",
        "RAIRE",
        name="auditmathtype",
    )
    new_audit_math_type_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE election ALTER COLUMN audit_math_type TYPE auditmathtype USING audit_math_type::text::auditmathtype"
    )

    op.execute("DROP TYPE auditmathtype_old")


def downgrade():  # pragma: no cover
    pass
