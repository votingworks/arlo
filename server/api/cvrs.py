import uuid
import io
import tempfile
import csv
from typing import Dict, Optional, TypedDict
from collections import defaultdict
import re
import difflib
import ast
from datetime import datetime
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, NotFound, Conflict

from . import api
from ..database import db_session, engine as db_engine
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..util.process_file import (
    process_file,
    serialize_file,
    serialize_file_processing,
    UserError,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import decode_csv_file
from ..util.group_by import group_by
from ..audit_math.suite import HybridPair


class CvrChoiceMetadata(TypedDict):
    num_votes: int
    column: int


class CvrContestMetadata(TypedDict):
    votes_allowed: int
    total_ballots_cast: int
    # { choice_name: CvrChoiceMetadata }
    choices: Dict[str, CvrChoiceMetadata]


# { contest_id: CvrContestMetadata }
CVR_CONTESTS_METADATA = Dict[str, CvrContestMetadata]  # pylint: disable=invalid-name


def validate_uploaded_cvrs(contest: Contest):
    choice_names = {choice.name for choice in contest.choices}

    for jurisdiction in contest.jurisdictions:
        contests_metadata = cvr_contests_metadata(jurisdiction)
        if contests_metadata is None:
            raise Exception("Some jurisdictions haven't uploaded their CVRs yet.")

        if contest.name not in contests_metadata:
            raise Exception(
                f"Couldn't find contest {contest.name} in the CVR for jurisdiction {jurisdiction.name}"
            )

        cvr_choice_names = contests_metadata[contest.name]["choices"].keys()
        missing_choice_names = choice_names - cvr_choice_names
        if len(missing_choice_names) > 0:
            raise Exception(
                f"Couldn't find some contest choices ({', '.join(sorted(missing_choice_names))})"
                f" in the CVR for jurisdiction {jurisdiction.name}"
            )


def are_uploaded_cvrs_valid(contest: Contest):
    try:
        validate_uploaded_cvrs(contest)
        return True
    except Exception:
        return False


# Wraps Jurisdiction.cvr_contest_metadata, applying any contest name
# standardizations in Jurisdiction.contest_name_standardizations. This wrapper
# should always be used for reading the metadata, so that the contest names
# from the CVR will match those selected by the AA.
def cvr_contests_metadata(
    jurisdiction: Jurisdiction,
) -> Optional[CVR_CONTESTS_METADATA]:
    metadata = typing_cast(
        Optional[CVR_CONTESTS_METADATA], jurisdiction.cvr_contests_metadata
    )
    if metadata is None:
        return None

    standardizations = typing_cast(
        Optional[Dict[str, str]], jurisdiction.contest_name_standardizations
    )
    standardizations = {
        cvr_contest_name: contest_name
        for contest_name, cvr_contest_name in (standardizations or {}).items()
        if cvr_contest_name
    }

    return {
        standardizations.get(cvr_contest_name, cvr_contest_name): contest_metadata
        for cvr_contest_name, contest_metadata in metadata.items()
    }


def set_contest_metadata_from_cvrs(contest: Contest):
    if not are_uploaded_cvrs_valid(contest):
        return

    contest.choices = []

    for jurisdiction in contest.jurisdictions:
        metadata = cvr_contests_metadata(jurisdiction)
        assert metadata is not None
        contest_metadata = metadata[contest.name]

        if len(contest.choices) == 0:
            contest.choices = [
                ContestChoice(
                    id=str(uuid.uuid4()),
                    contest_id=contest.id,
                    name=choice_name,
                    num_votes=0,
                )
                for choice_name in contest_metadata["choices"]
            ]

        contest.votes_allowed = contest_metadata["votes_allowed"]
        for choice_name, choice_metadata in contest_metadata["choices"].items():
            choice = next(c for c in contest.choices if c.name == choice_name)
            choice.num_votes += choice_metadata["num_votes"]


# For Hybrid audits, we need to compute the vote counts for the CVRs
# specifically so we can subtract them from the total vote count and get the
# vote count for the non-CVR ballots.
def hybrid_contest_choice_vote_counts(
    contest: Contest,
) -> Optional[Dict[str, HybridPair]]:
    if not are_uploaded_cvrs_valid(contest):
        return None

    cvr_choice_votes = {choice.id: 0 for choice in contest.choices}
    for jurisdiction in contest.jurisdictions:
        metadata = cvr_contests_metadata(jurisdiction)
        assert metadata is not None
        contest_metadata = metadata[contest.name]
        for choice_name, choice_metadata in contest_metadata["choices"].items():
            choice = next(c for c in contest.choices if c.name == choice_name)
            cvr_choice_votes[choice.id] += choice_metadata["num_votes"]

    return {
        choice.id: HybridPair(
            cvr=cvr_choice_votes[choice.id],
            non_cvr=choice.num_votes - cvr_choice_votes[choice.id],
        )
        for choice in contest.choices
    }


def process_cvr_file(session: Session, jurisdiction: Jurisdiction, file: File):
    assert jurisdiction.cvr_file_id == file.id

    def process():
        if jurisdiction.cvr_file.contents == "":
            raise UserError("CVR file cannot be empty.")

        cvrs = csv.reader(
            io.StringIO(jurisdiction.cvr_file.contents, newline=None), delimiter=","
        )

        # Parse out all the initial metadata
        _election_name = next(cvrs)[0]
        contest_row = [" ".join(contest.splitlines()) for contest in next(cvrs)]
        first_contest_column = next(
            c for c, value in enumerate(contest_row) if value != ""
        )
        contest_headers = contest_row[first_contest_column:]
        contest_choices = next(cvrs)[first_contest_column:]
        _headers_and_affiliations = next(cvrs)

        # Contest headers look like this: "Presidential Primary (Vote For=1)"
        # We want to parse: contest_name="Presidential Primary", votes_allowed=1
        contest_names = []
        contest_votes_allowed = []
        for contest_header in contest_headers:
            match = re.match(r"^(.+) \(Vote For=(\d+)\)$", contest_header)
            if not match:
                raise UserError(
                    f"Invalid contest name: {contest_header}."
                    + " Contest names should have this format: Contest Name (Vote For=1)."
                )
            contest_names.append(match[1])
            contest_votes_allowed.append(int(match[2]))

        # Parse out metadata about the contests to store - we'll later use this
        # to populate the Contest object.
        contests_metadata = defaultdict(lambda: dict(choices=dict()))
        for column, (contest_name, votes_allowed, choice_name) in enumerate(
            zip(contest_names, contest_votes_allowed, contest_choices)
        ):
            contests_metadata[contest_name]["votes_allowed"] = votes_allowed
            contests_metadata[contest_name]["choices"][choice_name] = dict(
                # Store the column index of this contest choice so we can parse
                # interpretations later
                column=column,
                num_votes=0,  # Will be counted below
            )
            # Will be counted below
            contests_metadata[contest_name]["total_ballots_cast"] = 0

        batches_by_key = {
            (batch.tabulator, batch.name): batch for batch in jurisdiction.batches
        }

        # Parse ballot rows and store them as CvrBallots. Since we may have
        # millions of rows, we write this data into a tempfile and load it into
        # the db using the COPY command (muuuuch faster than INSERT).
        with tempfile.TemporaryFile(mode="w+") as ballots_tempfile:
            ballots_csv = csv.writer(ballots_tempfile)

            for row in cvrs:
                [
                    cvr_number,
                    tabulator_number,
                    batch_id,
                    record_id,
                    imprinted_id,
                    *_,  # CountingGroup (maybe), PrecintPortion, BallotType
                ] = row[:first_contest_column]
                interpretations = row[first_contest_column:]

                db_batch = batches_by_key.get((tabulator_number, batch_id))

                if not db_batch:
                    close_matches = difflib.get_close_matches(
                        str((tabulator_number, batch_id)),
                        (str(batch_key) for batch_key in batches_by_key),
                        n=1,
                    )
                    closest_match = (
                        ast.literal_eval(close_matches[0]) if close_matches else None
                    )

                    raise UserError(
                        "Invalid TabulatorNum/BatchId for row with"
                        f" CvrNumber {cvr_number}: {tabulator_number}, {batch_id}."
                        " The TabulatorNum and BatchId fields in the CVR file"
                        " must match the Tabulator and Batch Name fields in the"
                        " ballot manifest."
                        + (
                            (
                                " The closest match we found in the ballot manifest was:"
                                f" {closest_match[0]}, {closest_match[1]}."
                            )
                            if closest_match
                            else ""
                        )
                        + " Please check your CVR file and ballot manifest thoroughly"
                        " to make sure these values match - there may be a similar"
                        " inconsistency in other rows in the CVR file."
                    )

                # For hybrid audits, skip any batches that were marked as not
                # having CVRs in the manifest
                if (
                    jurisdiction.election.audit_type == AuditType.HYBRID
                    and not db_batch.has_cvrs
                ):
                    continue

                ballots_csv.writerow(
                    [
                        db_batch.id,
                        record_id,
                        imprinted_id,
                        # Store the raw interpretation columns to save time/space -
                        # we can parse them on demand for just the ballots that get
                        # sampled using the contest metadata we stored above
                        ",".join(interpretations),
                    ]
                )

                # Add to our running totals for ContestChoice.num_votes and
                # Contest.total_ballots_cast
                contests_on_ballot = set()
                interpretations_by_contest = group_by(
                    zip(contest_names, contest_choices, interpretations),
                    key=lambda tuple: tuple[0],  # contest_name
                )
                for contest_name, interpretations in interpretations_by_contest.items():
                    # Skip contests not on ballot
                    if any(
                        interpretation == "" for _, _, interpretation in interpretations
                    ):
                        continue
                    contests_on_ballot.add(contest_name)

                    # Skip overvotes
                    votes = sum(
                        int(interpretation) for _, _, interpretation in interpretations
                    )
                    if votes > contests_metadata[contest_name]["votes_allowed"]:
                        continue

                    for _, choice_name, interpretation in interpretations:
                        contests_metadata[contest_name]["choices"][choice_name][
                            "num_votes"
                        ] += int(interpretation)

                for contest_name in contests_on_ballot:
                    contests_metadata[contest_name]["total_ballots_cast"] += 1

            jurisdiction.cvr_contests_metadata = contests_metadata

            # In order to use COPY, we have to bypass SQLAlchemy and use
            # the underlying DBAPI (psycogp2). This means these commands
            # will happen in a separate transaction from the surrounding
            # context.
            connection = db_engine.raw_connection()
            try:
                cursor = connection.cursor()
                cursor.execute("BEGIN")
                ballots_tempfile.seek(0)
                cursor.copy_expert(
                    """
                        COPY cvr_ballot (
                            batch_id,
                            record_id,
                            imprinted_id,
                            interpretations
                        )
                        FROM STDIN
                        WITH (
                            FORMAT CSV,
                            DELIMITER ','
                        )
                        """,
                    ballots_tempfile,
                )
                cursor.execute("COMMIT")
                cursor.close()
                connection.commit()
            except Exception as exc:
                cursor.execute("ROLLBACK")
                raise exc
            finally:
                connection.close()

        # Assign ballot_position for each CvrBallot by counting each ballot's
        # index within the batch in the CVR, ordering by record_id within the
        # batch
        ballot_position = (
            CvrBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction.id)
            .with_entities(
                CvrBallot.batch_id,
                CvrBallot.record_id,
                func.row_number()
                .over(partition_by=CvrBallot.batch_id, order_by=CvrBallot.record_id)
                .label("ballot_position"),
            )
            .subquery()
        )
        db_session.execute(
            CvrBallot.__table__.update()  # pylint: disable=no-member
            .values(ballot_position=ballot_position.c.ballot_position)
            .where(
                and_(
                    CvrBallot.batch_id == ballot_position.c.batch_id,
                    CvrBallot.record_id == ballot_position.c.record_id,
                )
            )
        )

        if jurisdiction.election.audit_type == AuditType.BALLOT_COMPARISON:
            for contest in jurisdiction.election.contests:
                set_contest_metadata_from_cvrs(contest)

    # Until we add validation/error handling to our CVR parsing, we'll just
    # catch all errors and wrap them with a generic message.
    def process_catch_exceptions():
        try:
            process()
        except Exception as exc:
            if isinstance(exc, UserError):
                raise exc
            raise Exception("Could not parse CVR file") from exc

    process_file(session, file, process_catch_exceptions)


# Raises if invalid
def validate_cvr_upload(
    request: Request, election: Election, jurisdiction: Jurisdiction
):
    if election.audit_type not in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        raise Conflict("Can't upload CVR file for this audit type.")

    if not jurisdiction.manifest_file_id:
        raise Conflict("Must upload ballot manifest before uploading CVR file.")

    if "cvrs" not in request.files:
        raise BadRequest("Missing required file parameter 'cvrs'")


# We save the CVR file, and bgcompute finds it and processes it in
# the background.
def save_cvr_file(cvr, jurisdiction: Jurisdiction):
    cvr_string = decode_csv_file(cvr.read())
    jurisdiction.cvr_file = File(
        id=str(uuid.uuid4()),
        name=cvr.filename,
        contents=cvr_string,
        uploaded_at=datetime.now(timezone.utc),
    )


def clear_cvr_file(jurisdiction: Jurisdiction):
    if jurisdiction.cvr_file_id:
        File.query.filter_by(id=jurisdiction.cvr_file_id).delete()
        CvrBallot.query.filter(
            CvrBallot.batch_id.in_(
                Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
                .with_entities(Batch.id)
                .subquery()
            )
        ).delete(synchronize_session=False)
        jurisdiction.cvr_contests_metadata = None


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs", methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def upload_cvrs(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_cvr_upload(request, election, jurisdiction)
    clear_cvr_file(jurisdiction)
    save_cvr_file(request.files["cvrs"], jurisdiction)
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs", methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_cvrs(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify(
        file=serialize_file(jurisdiction.cvr_file),
        processing=serialize_file_processing(jurisdiction.cvr_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs/csv", methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_cvr_file(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if not jurisdiction.cvr_file:
        return NotFound()

    return csv_response(jurisdiction.cvr_file.contents, jurisdiction.cvr_file.name)


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs", methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_cvrs(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_cvr_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
