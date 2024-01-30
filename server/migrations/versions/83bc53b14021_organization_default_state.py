# pylint: disable=invalid-name
"""Organization.default_state

Revision ID: 83bc53b14021
Revises: fea3ed38fb6c
Create Date: 2023-10-03 17:42:40.952614+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "83bc53b14021"
down_revision = "fea3ed38fb6c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organization", sa.Column("default_state", sa.String(length=100), nullable=True)
    )


def downgrade():
    pass  # pragma: no cover
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_column('organization', 'default_state')
    # ### end Alembic commands ###