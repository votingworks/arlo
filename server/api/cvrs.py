import uuid
import io
import tempfile
import csv
import typing
from collections import defaultdict
import re
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
)
from ..util.csv_download import csv_response
from ..util.csv_parse import decode_csv_file
from ..util.jsonschema import JSONDict
from ..util.group_by import group_by


def set_contest_metadata_from_cvrs(contest: Contest):
    # Only set the contest metadata if it hasn't been set already
    if contest.total_ballots_cast is not None:
        return

    contest.total_ballots_cast = 0

    for jurisdiction in contest.jurisdictions:
        cvr_contests_metadata = typing.cast(
            JSONDict, jurisdiction.cvr_contests_metadata
        )
        if not cvr_contests_metadata or contest.name not in cvr_contests_metadata:
            raise Conflict("Some jurisdictions haven't uploaded their CVRs yet.")

        contest_metadata = cvr_contests_metadata[contest.name]

        if not contest.choices:
            contest.choices = [
                ContestChoice(
                    id=str(uuid.uuid4()),
                    contest_id=contest.id,
                    name=choice_name,
                    num_votes=0,
                )
                for choice_name in contest_metadata["choices"]
            ]

        contest.total_ballots_cast += contest_metadata["total_ballots_cast"]
        contest.votes_allowed = contest_metadata["votes_allowed"]
        for choice_name, choice_metadata in contest_metadata["choices"].items():
            choice = next(c for c in contest.choices if c.name == choice_name)
            choice.num_votes += choice_metadata["num_votes"]


def process_cvr_file(session: Session, jurisdiction: Jurisdiction, file: File):
    assert jurisdiction.cvr_file_id == file.id

    def process():
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

        batch_key_to_id = {
            (batch.tabulator, batch.name): batch.id for batch in jurisdiction.batches
        }

        # Parse ballot rows and store them as CvrBallots. Since we may have
        # millions of rows, we write this data into a tempfile and load it into
        # the db using the COPY command (muuuuch faster than INSERT).
        with tempfile.TemporaryFile(mode="w+") as ballots_tempfile:
            ballots_csv = csv.writer(ballots_tempfile)
            ballots_csv.writerow(
                ["batch_id", "ballot_position", "imprinted_id", "interpretations"]
            )

            for row in cvrs:
                [
                    _cvr_number,
                    tabulator_number,
                    batch_id,
                    record_id,
                    imprinted_id,
                    *_,  # CountingGroup (maybe), PrecintPortion, BallotType
                ] = row[:first_contest_column]
                interpretations = row[first_contest_column:]
                db_batch_id = batch_key_to_id[(tabulator_number, batch_id)]
                ballots_csv.writerow(
                    [
                        db_batch_id,
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
                        COPY cvr_ballot
                        FROM STDIN
                        WITH (
                            FORMAT CSV,
                            DELIMITER ',',
                            HEADER
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

    # Until we add validation/error handling to our CVR parsing, we'll just
    # catch all errors and wrap them with a generic message.
    def process_catch_exceptions():
        try:
            process()
        except Exception as exc:
            raise Exception("Could not parse CVR file") from exc

    process_file(session, file, process_catch_exceptions)


# Raises if invalid
def validate_cvr_upload(
    request: Request, election: Election, jurisdiction: Jurisdiction
):
    if election.audit_type != AuditType.BALLOT_COMPARISON:
        raise Conflict("Can only upload CVR file for ballot comparison audits.")

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
