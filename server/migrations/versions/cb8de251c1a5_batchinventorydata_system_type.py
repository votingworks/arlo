# pylint: disable=invalid-name
"""BatchInventoryData.system_type

Revision ID: cb8de251c1a5
Revises: c012fa6b13a9
Create Date: 2024-03-27 19:17:15.548250+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cb8de251c1a5"
down_revision = "c012fa6b13a9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "batch_inventory_data",
        sa.Column("system_type", sa.String(length=200), nullable=True),
    )

    # Populate the field for existing BatchInventoryData entries
    op.execute(
        """
        UPDATE batch_inventory_data
        SET system_type = 'DOMINION'
        """
    )


def downgrade():  # pragma: no cover
    pass
