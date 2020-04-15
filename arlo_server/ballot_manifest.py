import csv, io, locale, uuid
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest
from datetime import datetime

from arlo_server import app
from arlo_server.models import (
    db,
    Batch,
    Election,
    File,
    Jurisdiction,
)
from arlo_server.auth import with_jurisdiction_access
from util.process_file import (
    process_file,
    serialize_file,
    serialize_file_processing,
    UserError,
)

BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
STORAGE_LOCATION = "Storage Location"
TABULATOR = "Tabulator"


def process_ballot_manifest_file(
    session: Session, jurisdiction: Jurisdiction, file: File
):
    assert jurisdiction.manifest_file_id == file.id

    def process():
        manifest_csv = csv.DictReader(io.StringIO(file.contents))

        missing_fields = [
            field
            for field in [BATCH_NAME, NUMBER_OF_BALLOTS]
            if field not in manifest_csv.fieldnames
        ]

        if missing_fields:
            raise UserError(f"Missing required CSV fields: {', '.join(missing_fields)}")

        num_batches = 0
        num_ballots = 0
        for row in manifest_csv:
            num_ballots_in_batch_csv = row[NUMBER_OF_BALLOTS]

            try:
                num_ballots_in_batch = locale.atoi(num_ballots_in_batch_csv)
            except ValueError as error:
                raise UserError(
                    f"Invalid value for '{NUMBER_OF_BALLOTS}' on line {manifest_csv.line_num}: {num_ballots_in_batch_csv}"
                ) from error

            batch = Batch(
                id=str(uuid.uuid4()),
                name=row[BATCH_NAME],
                jurisdiction_id=jurisdiction.id,
                num_ballots=num_ballots_in_batch,
                storage_location=row.get(STORAGE_LOCATION) or None,
                tabulator=row.get(TABULATOR) or None,
            )
            session.add(batch)
            num_batches += 1
            num_ballots += batch.num_ballots

        jurisdiction.manifest_num_ballots = num_ballots
        jurisdiction.manifest_num_batches = num_batches

    process_file(session, file, process)

    election = jurisdiction.election

    # If we're in the single-jurisdiction flow, posting the ballot manifest
    # starts the first round, so we need to sample the ballots.
    # In the multi-jurisdiction flow, this happens after all jurisdictions
    # upload manifests, and is triggered by a different endpoint.
    if not election.is_multi_jurisdiction:
        # Import this here to avoid circular dependencies
        from arlo_server.routes import sample_ballots

        sample_ballots(session, election, election.rounds[0])


# Raises if invalid
def validate_ballot_manifest_upload(request: Request):
    if "manifest" not in request.files:
        raise BadRequest("Missing required file parameter 'manifest'")


# We save the ballot manifest file, and bgcompute finds it and processes it in
# the background.
def save_ballot_manifest_file(manifest: File, jurisdiction: Jurisdiction):
    manifest_string = manifest.read().decode("utf-8-sig")
    jurisdiction.manifest_file = File(
        id=str(uuid.uuid4()),
        name=manifest.filename,
        contents=manifest_string,
        uploaded_at=datetime.utcnow(),
    )


def clear_ballot_manifest_file(jurisdiction: Jurisdiction):
    jurisdiction.manifest_num_ballots = None
    jurisdiction.manifest_num_batches = None

    if jurisdiction.manifest_file_id:
        File.query.filter_by(id=jurisdiction.manifest_file_id).delete()
    Batch.query.filter_by(jurisdiction=jurisdiction).delete()


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["PUT"],
)
@with_jurisdiction_access
def upload_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_ballot_manifest_upload(request)
    clear_ballot_manifest_file(jurisdiction)
    save_ballot_manifest_file(request.files["manifest"], jurisdiction)
    db.session.commit()
    return jsonify(status="ok")


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["GET"],
)
@with_jurisdiction_access
def get_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if jurisdiction.manifest_file:
        return jsonify(
            file=serialize_file(jurisdiction.manifest_file),
            processing=serialize_file_processing(jurisdiction.manifest_file),
        )
    else:
        return jsonify(file=None, processing=None)


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["DELETE"],
)
@with_jurisdiction_access
def clear_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_ballot_manifest_file(jurisdiction)
    db.session.commit()
    return jsonify(status="ok")
