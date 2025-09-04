"""Remove batch comparison audit boards

Revision ID: fed66f26125e
Revises: 848293b46b37
Create Date: 2022-10-11 20:52:29.685082+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fed66f26125e"
down_revision = "848293b46b37"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("batch_audit_board_id_fkey", "batch", type_="foreignkey")
    op.drop_column("batch", "audit_board_id")


def downgrade():  # pragma: no cover
    pass
