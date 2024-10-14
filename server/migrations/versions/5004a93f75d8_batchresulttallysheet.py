# pylint: disable=invalid-name
"""BatchResultTallySheet

Revision ID: 5004a93f75d8
Revises: cec7ecc73bd8
Create Date: 2022-05-02 22:25:04.648947+00:00

"""
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5004a93f75d8"
down_revision = "cec7ecc73bd8"
branch_labels = None
depends_on = None


def upgrade():
    # Create batch_result_tally_sheet table
    op.create_table(
        "batch_result_tally_sheet",
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("batch_id", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batch.id"],
            name=op.f("batch_result_tally_sheet_batch_id_fkey"),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("batch_result_tally_sheet_pkey")),
        sa.UniqueConstraint(
            "batch_id", "name", name=op.f("batch_result_tally_sheet_batch_id_name_key")
        ),
    )
    # Link to batch_result
    op.add_column(
        "batch_result",
        sa.Column("tally_sheet_id", sa.String(length=200)),
    )
    op.create_foreign_key(
        op.f("batch_result_tally_sheet_id_fkey"),
        "batch_result",
        "batch_result_tally_sheet",
        ["tally_sheet_id"],
        ["id"],
        ondelete="cascade",
    )

    # Migrate existing batch results to a single tally sheet
    connection = op.get_bind()
    batches_with_results = connection.execute(
        """
        SELECT DISTINCT ON (id) id, batch_result.created_at FROM batch
        JOIN batch_result ON batch.id = batch_result.batch_id
        """
    )
    for batch_id, created_at in batches_with_results.fetchall():  # pragma: no cover
        tally_sheet_id = str(uuid.uuid4())
        connection.execute(
            f"""
            INSERT INTO batch_result_tally_sheet (id, batch_id, name, created_at, updated_at)
            VALUES ('{tally_sheet_id}', '{batch_id}', 'Tally Sheet #1', '{created_at}', '{created_at}')
            """
        )
        connection.execute(
            f"""
            UPDATE batch_result
            SET tally_sheet_id = '{tally_sheet_id}'
            WHERE batch_id = '{batch_id}'
            """
        )
    op.alter_column("batch_result", "tally_sheet_id", nullable=False)

    # Drop the old batch_result.batch_id column
    op.drop_constraint("batch_result_batch_id_fkey", "batch_result", type_="foreignkey")
    op.drop_column("batch_result", "batch_id")


def downgrade():  # pragma: no cover
    pass
