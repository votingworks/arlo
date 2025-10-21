"""add_batch_file_bundle_table

Revision ID: 4b1bf0241301
Revises: 6bd43f181daa
Create Date: 2025-10-13 23:30:16.662345+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4b1bf0241301"
down_revision = "6bd43f181daa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "batch_file_bundle",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("election_id", sa.String(length=200), nullable=False),
        sa.Column("bundle_type", sa.String(length=50), nullable=False),
        sa.Column("file_id", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["election_id"], ["election.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["file.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("election_id", "bundle_type", "created_at"),
    )


def downgrade():
    op.drop_table("batch_file_bundle")
