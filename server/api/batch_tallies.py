from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional, Tuple
import csv
import io
import uuid
from flask import request, jsonify, Request, session
from werkzeug.exceptions import BadRequest, NotFound, Conflict
from sqlalchemy.orm import Session

from . import api
from ..database import db_session, engine
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType, get_loggedin_user, get_support_user
from ..worker.tasks import (
    UserError,
    background_task,
    create_background_task,
)
from ..util.file import (
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    store_file,
    timestamp_filename,
)
from ..util.csv_download import (
    csv_response,
    election_timestamp_name,
    jurisdiction_timestamp_name,
)
from ..util.csv_parse import (
    parse_csv,
    CSVValueType,
    CSVColumnType,
    validate_csv_mimetype,
)
from ..util.string import format_count
from ..activity_log.activity_log import UploadFile, activity_base, record_activity


# { (contest_id, choice_id): csv_header }
ContestChoiceCsvHeaders = Dict[Tuple[str, str], str]

BATCH_NAME = "Batch Name"


def construct_contest_choice_csv_headers(
    election: Election,
    jurisdiction: Optional[Jurisdiction] = None,
) -> ContestChoiceCsvHeaders:
    audit_contests = list(election.contests)
    contests = audit_contests if jurisdiction is None else list(jurisdiction.contests)
    is_multi_contest_audit = len(audit_contests) > 1
    contest_choice_csv_headers = {
        # Include contest name in contest choice CSV headers for multi-contest audits just in
        # case two choices in different contests have the same name
        (contest.id, choice.id): (
            f"{contest.name} - {choice.name}" if is_multi_contest_audit else choice.name
        )
        for contest in contests
        for choice in contest.choices
    }
    return contest_choice_csv_headers


@background_task
def process_batch_tallies_file(
    jurisdiction_id: str,
    user: Tuple[UserType, str],
    support_user_email: Optional[str],
):
    jurisdiction: Jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    def process_batch_tallies_for_contest(
        contest: Contest,
        # { (contest_id, choice_id): csv_header }
        contest_choice_csv_headers: Dict[Tuple[str, str], str],
    ):
        columns = [CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True)] + [
            CSVColumnType(contest_choice_csv_header, CSVValueType.NUMBER)
            for contest_choice_csv_header in contest_choice_csv_headers.values()
        ]

        batch_tallies_file = retrieve_file(jurisdiction.batch_tallies_file.storage_path)
        batch_tallies_csv = list(parse_csv(batch_tallies_file, columns))
        batch_tallies_file.close()

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
        assert contest.votes_allowed is not None
        for row in batch_tallies_csv:
            allowed_tallies = (
                num_ballots_by_batch[row[BATCH_NAME]] * contest.votes_allowed
            )
            total_tallies = sum(
                int(row[contest_choice_csv_headers[(contest.id, choice.id)]])
                for choice in contest.choices
            )
            if total_tallies > allowed_tallies:
                raise UserError(
                    f'The total votes for contest "{contest.name}" in batch "{row[BATCH_NAME]}" '
                    f"({format_count(total_tallies, 'vote', 'votes')}) "
                    f"cannot exceed {allowed_tallies} - "
                    f"the number of ballots from the manifest "
                    f"({format_count(num_ballots_by_batch[row[BATCH_NAME]], 'ballot', 'ballots')}) "
                    f"multiplied by the number of votes allowed for the contest "
                    f"({format_count(contest.votes_allowed, 'vote', 'votes')} per ballot)."
                )

        return {
            row[BATCH_NAME]: {
                "ballots": num_ballots_by_batch[row[BATCH_NAME]],
                **{
                    choice.id: row[contest_choice_csv_headers[(contest.id, choice.id)]]
                    for choice in contest.choices
                },
            }
            for row in batch_tallies_csv
        }

    def process() -> None:
        contests = list(jurisdiction.contests)
        contest_choice_csv_headers = construct_contest_choice_csv_headers(
            jurisdiction.election, jurisdiction
        )

        # Save the tallies as a JSON blob in the format needed by the audit_math.macro module
        # { batch_name: { contest_id: { choice_id: vote_count } } }
        batch_tallies: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(dict)
        for contest in contests:
            batch_tallies_for_contest = process_batch_tallies_for_contest(
                contest, contest_choice_csv_headers
            )
            for batch_name, batch_votes in batch_tallies_for_contest.items():
                batch_tallies[batch_name][contest.id] = batch_votes

        jurisdiction.batch_tallies = batch_tallies

    error = None
    try:
        process()
    except Exception as exc:
        error = str(exc) or str(exc.__class__.__name__)
        raise exc
    finally:
        session = Session(engine)
        base = activity_base(jurisdiction.election)
        base.user_type, base.user_key = user
        base.support_user_email = support_user_email
        record_activity(
            UploadFile(
                timestamp=jurisdiction.batch_tallies_file.uploaded_at,
                base=base,
                jurisdiction_id=jurisdiction.id,
                jurisdiction_name=jurisdiction.name,
                file_type="batch_tallies",
                error=error,
            ),
            session,
        )
        session.commit()


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

    validate_csv_mimetype(request.files["batchTallies"])


def clear_batch_tallies_data(jurisdiction: Jurisdiction):
    jurisdiction.batch_tallies = None


def reprocess_batch_tallies_file_if_uploaded(
    jurisdiction: Jurisdiction,
    user: Tuple[UserType, str],
    support_user_email: Optional[str],
):
    if jurisdiction.batch_tallies_file:
        clear_batch_tallies_data(jurisdiction)
        jurisdiction.batch_tallies_file.task = create_background_task(
            process_batch_tallies_file,
            dict(
                jurisdiction_id=jurisdiction.id,
                user=user,
                support_user_email=support_user_email,
            ),
        )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["PUT"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def upload_batch_tallies(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_batch_tallies_upload(request, election, jurisdiction)

    clear_batch_tallies_data(jurisdiction)

    batch_tallies = request.files["batchTallies"]
    storage_path = store_file(
        batch_tallies.stream,
        f"audits/{jurisdiction.election_id}/jurisdictions/{jurisdiction.id}/"
        + timestamp_filename("batch_tallies", "csv"),
    )
    jurisdiction.batch_tallies_file = File(
        id=str(uuid.uuid4()),
        name=batch_tallies.filename,  # type: ignore
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    jurisdiction.batch_tallies_file.task = create_background_task(
        process_batch_tallies_file,
        dict(
            jurisdiction_id=jurisdiction.id,
            user=get_loggedin_user(session),
            support_user_email=get_support_user(session),
        ),
    )

    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    if not jurisdiction.batch_tallies_file:
        return NotFound()

    return csv_response(
        retrieve_file(jurisdiction.batch_tallies_file.storage_path),
        jurisdiction.batch_tallies_file.name,
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies",
    methods=["DELETE"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def clear_batch_tallies(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    if jurisdiction.batch_tallies_file:
        db_session.delete(jurisdiction.batch_tallies_file)
        clear_batch_tallies_data(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-tallies/template-csv",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def download_batch_tallies_template_csv(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    string_io = io.StringIO()
    template = csv.writer(string_io)

    contest_choice_csv_headers = construct_contest_choice_csv_headers(
        jurisdiction.election, jurisdiction
    )
    csv_headers = [
        BATCH_NAME,
        *contest_choice_csv_headers.values(),
    ]

    template.writerow(csv_headers)
    for i in range(0, 3):
        template.writerow([f"Batch {i + 1}"] + ["0"] * len(contest_choice_csv_headers))

    string_io.seek(0)
    return csv_response(
        string_io,
        filename=f"candidate-totals-by-batch-template-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


@api.route(
    "/election/<election_id>/batch-tallies/summed-by-jurisdiction-csv",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_batch_tallies_summed_by_jurisdiction_csv(election: Election):
    string_io = io.StringIO()
    csv_writer = csv.writer(string_io)

    contest_choice_csv_headers = construct_contest_choice_csv_headers(election)
    csv_headers = [
        "Jurisdiction",
        *contest_choice_csv_headers.values(),
        "Total Ballots",
    ]
    csv_writer.writerow(csv_headers)

    running_totals = [0] * (len(contest_choice_csv_headers) + 1)
    for jurisdiction in election.jurisdictions:
        # Sum vote counts across batches
        # { (contest_id, choice_id): vote_count }
        vote_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        if jurisdiction.batch_tallies is not None:
            assert not isinstance(jurisdiction.batch_tallies, list)
            for batch_tallies in jurisdiction.batch_tallies.values():
                for contest_id, batch_tallies_for_contest in batch_tallies.items():
                    for choice_id, vote_count in batch_tallies_for_contest.items():
                        vote_counts[(contest_id, choice_id)] += vote_count

        batches = list(jurisdiction.batches)
        total_ballot_count = (
            sum(batch.num_ballots for batch in batches) if len(batches) > 0 else None
        )

        counts = [
            vote_counts.get(key, None) for key in contest_choice_csv_headers.keys()
        ] + [total_ballot_count]

        row = [jurisdiction.name, *counts]
        csv_writer.writerow(row)

        running_totals = [
            running_total + (count or 0)
            for running_total, count in zip(running_totals, counts)
        ]

    total_row = ["Total", *running_totals]
    csv_writer.writerow(total_row)

    string_io.seek(0)
    return csv_response(
        string_io,
        filename=f"reported-results-{election_timestamp_name(election)}.csv",
    )
