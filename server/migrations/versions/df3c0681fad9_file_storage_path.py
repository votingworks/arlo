"""File.storage_path

Revision ID: df3c0681fad9
Revises: 266fba5a5c8a
Create Date: 2021-11-29 23:39:40.181378+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "df3c0681fad9"
down_revision = "266fba5a5c8a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("file", sa.Column("storage_path", sa.String(length=250)))


def downgrade():  # pragma: no cover
    pass
