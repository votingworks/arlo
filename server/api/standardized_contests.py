import uuid
import re
import typing
from datetime import datetime
from typing import Dict, Optional
from collections import defaultdict
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
CHOICE_NAMES = "Choice Names"

STANDARDIZED_CONTEST_COLUMNS = [
    CSVColumnType(CONTEST_NAME, CSVValueType.TEXT, unique=True),
    CSVColumnType(JURISDICTIONS, CSVValueType.TEXT),
    # This column is optional, but if included, every row has to have a value
    CSVColumnType(
        CHOICE_NAMES, CSVValueType.TEXT, required_column=False, allow_empty_rows=False
    ),
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

        parsed_row = dict(
            name=contest_name,
            jurisdictionIds=[jurisdiction.id for jurisdiction in jurisdictions],
        )

        # This will either be true for all rows or no rows, per the STANDARDIZED_CONTEST_COLUMNS
        # schema
        if CHOICE_NAMES in row:  # pragma: no cover
            choice_names = [
                choice_name.strip()
                for choice_name in row[CHOICE_NAMES].split(";")
                if choice_name.strip() != ""
            ]
            parsed_row["choiceNames"] = choice_names

        standardized_contests.append(parsed_row)

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

    # Update contest choice name standardizations to account for changes to choice names in
    # standardized contests file
    for jurisdiction in election.jurisdictions:  # pragma: no cover
        contest_choice_name_standardizations = (
            typing.cast(
                Optional[Dict[str, Dict[str, Optional[str]]]],
                jurisdiction.contest_choice_name_standardizations,
            )
            or {}
        )

        updated_contest_choice_name_standardizations = typing.cast(
            Dict[str, Dict[str, Optional[str]]], defaultdict(dict)
        )
        for contest in election.contests:
            if contest.id not in contest_choice_name_standardizations:
                continue

            standardized_contest_choice_names = next(
                (
                    standardized_contest.get("choiceNames", None)
                    for standardized_contest in standardized_contests
                    if standardized_contest["name"] == contest.name
                ),
                None,
            )

            if standardized_contest_choice_names is None:
                continue

            for cvr_choice_name, choice_name in contest_choice_name_standardizations[
                contest.id
            ].items():
                # Carry over all standardizations for which:
                # 1. The standardized contest still exists
                # 2. The CVR choice name is still in need of standardization
                # 3. The selected choice name is still a valid option
                if (
                    cvr_choice_name not in standardized_contest_choice_names
                    and choice_name in standardized_contest_choice_names
                ):
                    updated_contest_choice_name_standardizations[contest.id][
                        cvr_choice_name
                    ] = choice_name

        jurisdiction.contest_choice_name_standardizations = (
            updated_contest_choice_name_standardizations
        ) or None

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
        name=file.filename,  # type: ignore
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
