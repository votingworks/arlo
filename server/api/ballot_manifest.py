import locale, uuid
from datetime import datetime
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, NotFound

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_jurisdiction_access, with_election_access
from ..util.process_file import (
    process_file,
    serialize_file,
    serialize_file_processing,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import decode_csv_file, parse_csv, CSVValueType, CSVColumnType

BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
STORAGE_LOCATION = "Storage Location"
TABULATOR = "Tabulator"

BALLOT_MANIFEST_COLUMNS = [
    CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True),
    CSVColumnType(NUMBER_OF_BALLOTS, CSVValueType.NUMBER),
    CSVColumnType(STORAGE_LOCATION, CSVValueType.TEXT, required=False),
    CSVColumnType(TABULATOR, CSVValueType.TEXT, required=False),
]


def process_ballot_manifest_file(
    session: Session, jurisdiction: Jurisdiction, file: File
):
    assert jurisdiction.manifest_file_id == file.id

    def process():
        manifest_csv = parse_csv(
            jurisdiction.manifest_file.contents, BALLOT_MANIFEST_COLUMNS
        )

        num_batches = 0
        num_ballots = 0
        for row in manifest_csv:
            num_ballots_in_batch_csv = row[NUMBER_OF_BALLOTS]
            num_ballots_in_batch = locale.atoi(num_ballots_in_batch_csv)

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
        # pylint: disable=import-outside-toplevel,cyclic-import
        from .routes import sample_ballots

        sample_ballots(session, election, list(election.rounds)[0])


# Raises if invalid
def validate_ballot_manifest_upload(request: Request):
    if "manifest" not in request.files:
        raise BadRequest("Missing required file parameter 'manifest'")


# We save the ballot manifest file, and bgcompute finds it and processes it in
# the background.
def save_ballot_manifest_file(manifest, jurisdiction: Jurisdiction):
    manifest_string = decode_csv_file(manifest.read())
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


@api.route(
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
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["GET"],
)
@with_jurisdiction_access
def get_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    if jurisdiction.manifest_file:
        return jsonify(
            file=serialize_file(jurisdiction.manifest_file),
            processing=serialize_file_processing(jurisdiction.manifest_file),
        )
    else:
        return jsonify(file=None, processing=None)


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest/csv",
    methods=["GET"],
)
@with_election_access
def download_ballot_manifest_file(
    election: Election, jurisdiction_id: str,  # pylint: disable=unused-argument
):
    jurisdiction = Jurisdiction.query.filter_by(
        election_id=election.id, id=jurisdiction_id
    ).first()
    if not jurisdiction or not jurisdiction.manifest_file:
        return NotFound()

    return csv_response(
        jurisdiction.manifest_file.contents, jurisdiction.manifest_file.name
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["DELETE"],
)
@with_jurisdiction_access
def clear_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_ballot_manifest_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
