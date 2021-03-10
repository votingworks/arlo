import uuid
from datetime import datetime
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, NotFound, Conflict

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..util.process_file import (
    process_file,
    serialize_file,
    serialize_file_processing,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import decode_csv_file, parse_csv, CSVValueType, CSVColumnType

CONTAINER = "Container"
TABULATOR = "Tabulator"
BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
CVR = "CVR"


def validate_uploaded_manifests(contest: Contest):
    for jurisdiction in contest.jurisdictions:
        if jurisdiction.manifest_num_ballots is None:
            raise Conflict("Some jurisdictions haven't uploaded their manifests yet")

        # TODO for ballot polling audits, validate total ballots across
        # manifests is greater than or equal to contest.total_ballots_cast
        # entered by the AA


def are_uploaded_manifests_valid(contest: Contest):
    try:
        validate_uploaded_manifests(contest)
        return True
    except Conflict:
        return False


def set_total_ballots_from_manifests(contest: Contest):
    if not are_uploaded_manifests_valid(contest):
        return

    contest.total_ballots_cast = sum(
        jurisdiction.manifest_num_ballots for jurisdiction in contest.jurisdictions
    )


def process_ballot_manifest_file(
    session: Session, jurisdiction: Jurisdiction, file: File
):
    assert jurisdiction.manifest_file_id == file.id

    def process():
        # In ballot comparison and hybrid audits, each batch is uniquely
        # identified by (tabulator, batch name). For other types of audits, the
        # batch name is unique.
        use_tabulator = jurisdiction.election.audit_type in [
            AuditType.BALLOT_COMPARISON,
            AuditType.HYBRID,
        ]
        # Hybrid audits need a CVR column to tell us which batches have CVRS
        # (for which we use ballot comparison math) and which don't (for which
        # we use ballot polling math).
        use_cvr = jurisdiction.election.audit_type == AuditType.HYBRID
        columns = [
            CSVColumnType(CONTAINER, CSVValueType.TEXT, required=False),
            CSVColumnType(
                TABULATOR,
                CSVValueType.TEXT,
                required=use_tabulator,
                unique=use_tabulator,
            ),
            CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True),
            CSVColumnType(NUMBER_OF_BALLOTS, CSVValueType.NUMBER),
            CSVColumnType(CVR, CSVValueType.YES_NO, required=use_cvr),
        ]

        manifest_csv = parse_csv(jurisdiction.manifest_file.contents, columns)

        num_batches = 0
        num_ballots = 0
        for row in manifest_csv:
            batch = Batch(
                id=str(uuid.uuid4()),
                name=row[BATCH_NAME],
                jurisdiction_id=jurisdiction.id,
                num_ballots=row[NUMBER_OF_BALLOTS],
                container=row.get(CONTAINER, None),
                tabulator=row.get(TABULATOR, None),
                has_cvrs=row.get(CVR, None),
            )
            session.add(batch)
            num_batches += 1
            num_ballots += batch.num_ballots

        jurisdiction.manifest_num_ballots = num_ballots
        jurisdiction.manifest_num_batches = num_batches

        if jurisdiction.election.audit_type != AuditType.BALLOT_POLLING:
            for contest in jurisdiction.contests:
                set_total_ballots_from_manifests(contest)

    process_file(session, file, process)


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
        uploaded_at=datetime.now(timezone.utc),
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
@restrict_access([UserType.JURISDICTION_ADMIN])
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
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify(
        file=serialize_file(jurisdiction.manifest_file),
        processing=serialize_file_processing(jurisdiction.manifest_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest/csv",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_ballot_manifest_file(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if not jurisdiction.manifest_file:
        return NotFound()

    return csv_response(
        jurisdiction.manifest_file.contents, jurisdiction.manifest_file.name
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_ballot_manifest_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
