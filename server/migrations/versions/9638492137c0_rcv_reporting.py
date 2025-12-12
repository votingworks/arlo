"""RCV reporting

Revision ID: 9638492137c0
Revises: ce0427619312
Create Date: 2025-12-12 05:35:58.965843+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9638492137c0"
down_revision = "ce0427619312"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("round", sa.Column("report_text", sa.Text(), nullable=True))


def downgrade():
    pass
