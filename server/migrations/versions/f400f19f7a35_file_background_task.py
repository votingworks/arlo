# pylint: disable=invalid-name
"""File background task

Revision ID: f400f19f7a35
Revises: de96efe4d679
Create Date: 2021-08-19 20:52:23.661647+00:00
"""
import json
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f400f19f7a35"
down_revision = "de96efe4d679"
branch_labels = None
depends_on = None


def backfill():  # pragma: no cover
    # Backfill a background task for all previous files
    connection = op.get_bind()

    def backfill_task_for_file(file_id, task_name, payload):
        if not file_id:
            return
        (new_task_id,) = connection.execute(
            f"""
            INSERT INTO background_task (
                id,
                task_name,
                payload,
                created_at,
                updated_at,
                started_at,
                completed_at,
                error
            )
            SELECT
                '{str(uuid.uuid4())}',
                '{task_name}',
                '{json.dumps(payload)}',
                created_at,
                created_at,
                processing_started_at,
                processing_completed_at,
                processing_error
            FROM file WHERE id = '{file_id}'
            RETURNING id
            """
        ).fetchone()
        connection.execute(
            f"""
            UPDATE file
            SET task_id = '{new_task_id}'
            WHERE id = '{file_id}'
            """
        )

    jurisdictions = connection.execute(
        "SELECT id, manifest_file_id, cvr_file_id, batch_tallies_file_id FROM jurisdiction"
    )
    for (
        jurisdiction_id,
        manifest_file_id,
        cvr_file_id,
        batch_tallies_file_id,
    ) in jurisdictions.fetchall():
        payload = dict(jurisdiction_id=jurisdiction_id)
        backfill_task_for_file(
            manifest_file_id, "process_ballot_manifest_file", payload
        )
        backfill_task_for_file(cvr_file_id, "process_cvr_file", payload)
        backfill_task_for_file(
            batch_tallies_file_id, "process_batch_tallies_file", payload
        )

    elections = connection.execute(
        "SELECT id, jurisdictions_file_id, standardized_contests_file_id FROM election"
    )
    for (
        election_id,
        jurisdictions_file_id,
        standardized_contests_file_id,
    ) in elections.fetchall():
        payload = dict(election_id=election_id)
        backfill_task_for_file(
            jurisdictions_file_id, "process_jurisdictions_file", payload
        )
        backfill_task_for_file(
            standardized_contests_file_id, "process_standardized_contests_file", payload
        )

    # Clean up any orphan files laying around (there really shouldn't be any, but there are a few)
    connection.execute("DELETE FROM file WHERE task_id IS NULL")


def upgrade():
    op.add_column("file", sa.Column("task_id", sa.String(length=200), nullable=True))
    op.create_foreign_key(
        op.f("file_task_id_fkey"),
        "file",
        "background_task",
        ["task_id"],
        ["id"],
    )

    backfill()

    op.drop_column("file", "processing_started_at")
    op.drop_column("file", "processing_completed_at")
    op.drop_column("file", "processing_error")


def downgrade():  # pragma: no cover
    pass
