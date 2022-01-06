import uuid
import re
from datetime import datetime
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .contests import set_contest_metadata
from ..worker.tasks import (
    UserError,
    background_task,
    create_background_task,
)
from ..util.csv_parse import (
    parse_csv,
    CSVColumnType,
    CSVValueType,
    validate_csv_mimetype,
)
from ..util.csv_download import csv_response
from ..util.file import (
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    store_file,
    timestamp_filename,
)

CONTEST_NAME = "Contest Name"
JURISDICTIONS = "Jurisdictions"

STANDARDIZED_CONTEST_COLUMNS = [
    CSVColumnType(CONTEST_NAME, CSVValueType.TEXT, unique=True),
    CSVColumnType(JURISDICTIONS, CSVValueType.TEXT),
]


@background_task
def process_standardized_contests_file(election_id: str):
    election = Election.query.get(election_id)
    standardized_contests_file = retrieve_file(
        election.standardized_contests_file.storage_path
    )
    standardized_contests_csv = parse_csv(
        standardized_contests_file, STANDARDIZED_CONTEST_COLUMNS
    )

    standardized_contests = []
    for row in standardized_contests_csv:
        if row[JURISDICTIONS].strip().lower() == "all":
            jurisdictions = election.jurisdictions
        else:
            jurisdiction_names = {
                name.strip() for name in row[JURISDICTIONS].split(",")
            }
            jurisdictions = list(
                Jurisdiction.query.filter_by(election_id=election.id)
                .filter(Jurisdiction.name.in_(jurisdiction_names))
                .order_by(Jurisdiction.name)
                .all()
            )

            if len(jurisdictions) < len(jurisdiction_names):
                invalid_jurisdictions = jurisdiction_names - {
                    jurisdiction.name for jurisdiction in jurisdictions
                }
                raise UserError(
                    f"Invalid jurisdictions for contest {row[CONTEST_NAME]}: {', '.join(sorted(invalid_jurisdictions))}"
                )

        contest_name = " ".join(row[CONTEST_NAME].splitlines())
        # Strip off Dominion's vote-for designation"
        if "Vote For=" in contest_name:
            match = re.match(r"^(.+) \(Vote For=(\d+)\)$", contest_name)
            if match:
                contest_name = match[1]

        standardized_contests.append(
            dict(
                name=contest_name,
                jurisdictionIds=[jurisdiction.id for jurisdiction in jurisdictions],
            )
        )

    standardized_contests_file.close()

    election.standardized_contests = standardized_contests

    # If any contests were already created based on an older version of the
    # standardized contests file, update them based on this new file.
    for contest in election.contests:
        standardized_contest = next(
            (
                standardized_contest
                for standardized_contest in standardized_contests
                if standardized_contest["name"] == contest.name
            ),
            None,
        )
        if standardized_contest is None:
            db_session.delete(contest)
        else:
            contest.jurisdictions = Jurisdiction.query.filter(
                Jurisdiction.id.in_(standardized_contest["jurisdictionIds"])
            ).all()

    set_contest_metadata(election)


def validate_standardized_contests_upload(request: Request, election: Election):
    if election.audit_type not in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        raise Conflict("Can't upload CVR file for this audit type.")

    if len(list(election.jurisdictions)) == 0:
        raise Conflict(
            "Must upload jurisdictions file before uploading standardized contests file."
        )

    if "standardized-contests" not in request.files:
        raise BadRequest("Missing required file parameter 'standardized-contests'")

    validate_csv_mimetype(request.files["standardized-contests"])


@api.route("/election/<election_id>/standardized-contests/file", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def upload_standardized_contests_file(election: Election):
    validate_standardized_contests_upload(request, election)

    election.standardized_contests = None
    file = request.files["standardized-contests"]
    storage_path = store_file(
        file.stream,
        f"audits/{election.id}/" + timestamp_filename("standardized_contests", "csv"),
    )
    election.standardized_contests_file = File(
        id=str(uuid.uuid4()),
        name=file.filename,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    election.standardized_contests_file.task = create_background_task(
        process_standardized_contests_file, dict(election_id=election.id)
    )
    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/standardized-contests/file", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_standardized_contests_file(election: Election):
    return jsonify(
        file=serialize_file(election.standardized_contests_file),
        processing=serialize_file_processing(election.standardized_contests_file),
    )


@api.route("/election/<election_id>/standardized-contests", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_standardized_contests(election: Election):
    return jsonify(election.standardized_contests)


@api.route("/election/<election_id>/standardized-contests/file/csv", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def download_standardized_contests_file(election: Election):
    if not election.standardized_contests_file:
        return NotFound()

    return csv_response(
        retrieve_file(election.standardized_contests_file.storage_path),
        election.standardized_contests_file.name,
    )
