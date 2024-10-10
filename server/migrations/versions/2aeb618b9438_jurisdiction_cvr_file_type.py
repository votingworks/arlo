# pylint: disable=invalid-name
"""Jurisdiction.cvr_file_type

Revision ID: 2aeb618b9438
Revises: 971d6d153879
Create Date: 2021-10-06 16:32:19.878853+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2aeb618b9438"
down_revision = "971d6d153879"
branch_labels = None
depends_on = None


def upgrade():
    cvr_file_type_enum = sa.dialects.postgresql.ENUM(
        "DOMINION", "CLEARBALLOT", name="cvrfiletype"
    )
    cvr_file_type_enum.create(op.get_bind())
    op.add_column(
        "jurisdiction",
        sa.Column(
            "cvr_file_type",
            cvr_file_type_enum,
            nullable=True,
        ),
    )


def downgrade():  # pragma: no cover
    pass
