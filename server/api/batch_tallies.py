from datetime import datetime
import uuid
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
    UserError,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import decode_csv_file, parse_csv, CSVValueType, CSVColumnType
from ..activity_log.activity_log import UploadFile, activity_base, record_activity

BATCH_NAME = "Batch Name"


def process_batch_tallies_file(
    session: Session, jurisdiction: Jurisdiction, file: File
):
    def process():
        # We only support one contest for batch audits, so we can just take the
        # first contest from the jurisdiction's universe.
        assert len(jurisdiction.contests) == 1
        contest = jurisdiction.contests[0]

        columns = [CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True)] + [
            CSVColumnType(choice.name, CSVValueType.NUMBER)
            for choice in contest.choices
        ]

        batch_tallies_csv = list(
            parse_csv(jurisdiction.batch_tallies_file.contents, columns)
        )

        # Validate that the batch names match the ballot manifest
        jurisdiction_batch_names = {batch.name for batch in jurisdiction.batches}
        tally_batch_names = {row[BATCH_NAME] for row in batch_tallies_csv}
        extra_batch_names = sorted(tally_batch_names - jurisdiction_batch_names)
        missing_batch_names = sorted(jurisdiction_batch_names - tally_batch_names)
        if extra_batch_names or missing_batch_names:
            raise UserError(
                "Batch names must match the ballot manifest file."
                + (
                    "\nFound extra batch names: " + ", ".join(extra_batch_names)
                    if extra_batch_names
                    else ""
                )
                + (
                    "\nFound missing batch names: " + ", ".join(missing_batch_names)
                    if missing_batch_names
                    else ""
                )
            )

        # Validate that the sum tallies for each batch don't exceed the allowed votes
        num_ballots_by_batch = {
            batch.name: batch.num_ballots for batch in jurisdiction.batches
        }
        for row in batch_tallies_csv:
            allowed_tallies = (
                num_ballots_by_batch[row[BATCH_NAME]] * contest.votes_allowed
            )
            total_tallies = sum(int(row[choice.name]) for choice in contest.choices)
            if total_tallies > allowed_tallies:
                raise UserError(
                    f'The total votes for batch "{row[BATCH_NAME]}" ({total_tallies} votes)'
                    + f" cannot exceed {allowed_tallies} - the number of ballots from the manifest"
                    + f" ({num_ballots_by_batch[row[BATCH_NAME]]} ballots) multipled by the number"
                    + f" of votes allowed for the contest ({contest.votes_allowed} votes per ballot)."
                )

        # Save the tallies as a JSON blob in the format needed by the
        # audit_math.macro module, so we can easily load it up and pass it in
        jurisdiction.batch_tallies = {
            row[BATCH_NAME]: {
                contest.id: {
                    "ballots": num_ballots_by_batch[row[BATCH_NAME]],
                    **{choice.id: row[choice.name] for choice in contest.choices},
                }
            }
            for row in batch_tallies_csv
        }

    process_file(session, file, process)

    assert file.processing_started_at
    record_activity(
        UploadFile(
            timestamp=file.processing_started_at,
            base=activity_base(jurisdiction.election),
            jurisdiction_id=jurisdiction.id,
            jurisdiction_name=jurisdiction.name,
            file_type="batch_tallies",
            error=file.processing_error,
        )
    )


# Raises if invalid
def validate_batch_tallies_upload(
    request: Request, election: Election, jurisdiction: Jurisdiction
):
    if election.audit_type != AuditType.BATCH_COMPARISON:
        raise Conflict(
            "Can only upload batch tallies file for batch comparison audits."
        )

    if len(list(jurisdiction.contests)) == 0:
        raise Conflict("Jurisdiction does not have any contests assigned")

    if not jurisdiction.manifest_file_id:
        raise Conflict("Must upload ballot manifest before uploading batch tallies.")

    if "batchTallies" not in request.files:
        raise BadRequest("Missing required file parameter 'batchTallies'")


def clear_batch_tallies_file(jurisdiction: Jurisdiction):
    if jurisdiction.batch_tallies_file:
        db_session.delete(jurisdiction.batch_tallies_file)
        jurisdiction.batch_tallies = None


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def upload_batch_tallies(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_batch_tallies_upload(request, election, jurisdiction)

    clear_batch_tallies_file(jurisdiction)

    # We save the batch tallies file, and bgcompute finds it and processes it in
    # the background.
    batch_tallies = request.files["batchTallies"]
    jurisdiction.batch_tallies_file = File(
        id=str(uuid.uuid4()),
        name=batch_tallies.filename,
        contents=decode_csv_file(batch_tallies),
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_batch_tallies(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify(
        file=serialize_file(jurisdiction.batch_tallies_file),
        processing=serialize_file_processing(jurisdiction.batch_tallies_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies/csv",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_batch_tallies_file(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if not jurisdiction.batch_tallies_file:
        return NotFound()

    return csv_response(
        jurisdiction.batch_tallies_file.contents, jurisdiction.batch_tallies_file.name
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_batch_tallies(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_batch_tallies_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
