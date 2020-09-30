import uuid
import io
import tempfile
import csv
from collections import defaultdict
import re
from datetime import datetime
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, NotFound

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
from ..util.group_by import group_by


def process_cvr_file(session: Session, jurisdiction: Jurisdiction, file: File):
    assert jurisdiction.cvr_file_id == file.id

    def process():
        cvrs = csv.reader(io.StringIO(jurisdiction.cvr_file.contents), delimiter=",")

        _election_name = next(cvrs)[0]

        contest_headers = next(cvrs)[7:]
        contest_choices = next(cvrs)[7:]
        headers_and_affiliations = next(cvrs)
        _headers = headers_and_affiliations[:7]
        affiliations = headers_and_affiliations[7:]

        contest_names = []
        contest_votes_allowed = []
        for contest_header in contest_headers:
            match = re.match(r"^(.+) \(Vote For=(\d+)\)$", contest_header)
            contest_names.append(match[1])
            contest_votes_allowed.append(match[2])

        vote_column_headers = list(
            zip(contest_names, contest_votes_allowed, contest_choices, affiliations)
        )

        contests_metadata = defaultdict(dict)
        for contest_name, choice_tuples in group_by(
            vote_column_headers, lambda h: h[0]  # contest_name
        ).items():
            contests_metadata[contest_name] = dict(
                votes_allowed=int(choice_tuples[0][1]),  # votes_allowed
                choices=[
                    (choice_name, affiliation)
                    for _, _, choice_name, affiliation in choice_tuples
                ],
            )
        jurisdiction.cvr_contests_metadata = contests_metadata

        batch_name_to_id = dict(
            Batch.query.filter_by(jurisdiction_id=jurisdiction.id).values(
                Batch.name, Batch.id
            )
        )

        with tempfile.TemporaryFile(mode="w+") as ballots_tempfile:
            with tempfile.TemporaryFile(mode="w+") as interpretations_tempfile:
                ballots_csv = csv.writer(ballots_tempfile)
                interpretations_csv = csv.writer(interpretations_tempfile)

                for row in cvrs:
                    [
                        _cvr_number,
                        tabulator_number,
                        batch_id,
                        record_id,
                        imprinted_id,
                        _precinct_portion,
                        _ballot_type,
                        *votes,
                    ] = row
                    db_batch_id = batch_name_to_id[f"{tabulator_number} - {batch_id}"]
                    ballots_csv.writerow([db_batch_id, record_id, imprinted_id])

                    for (contest_name, _, contest_choice, _), vote_str in zip(
                        vote_column_headers, votes
                    ):
                        is_voted_for = {"1": True, "0": False}.get(vote_str, None)
                        interpretations_csv.writerow(
                            [
                                db_batch_id,
                                record_id,
                                contest_name,
                                contest_choice,
                                is_voted_for,
                            ]
                        )

                ballots_tempfile.seek(0)
                interpretations_tempfile.seek(0)

                connection = db_engine.raw_connection()
                try:
                    cursor = connection.cursor()
                    cursor.execute(
                        f"""
                        DELETE FROM cvr_ballot
                        WHERE batch_id IN (
                            SELECT id FROM batch
                            WHERE jurisdiction_id = '{jurisdiction.id}'
                        );
                        """
                    )
                    cursor.copy_expert(
                        """
                        COPY cvr_ballot
                        FROM STDIN
                        WITH (
                            FORMAT CSV,
                            DELIMITER ','
                        );
                        """,
                        ballots_tempfile,
                    )
                    cursor.copy_expert(
                        """
                        COPY cvr_ballot_interpretation
                        FROM STDIN
                        WITH (
                            FORMAT CSV,
                            DELIMITER ','
                        );
                        """,
                        interpretations_tempfile,
                    )
                    cursor.close()
                    connection.commit()
                finally:
                    connection.close()

    process_file(session, file, process)


# Raises if invalid
def validate_cvr_upload(request: Request):  # pragma: no cover
    # TODO test
    if "cvr" not in request.files:
        raise BadRequest("Missing required file parameter 'cvr'")


# We save the CVR file, and bgcompute finds it and processes it in
# the background.
def save_cvr_file(cvr, jurisdiction: Jurisdiction):
    cvr_string = decode_csv_file(cvr.read())
    jurisdiction.cvr_file = File(
        id=str(uuid.uuid4()),
        name=cvr.filename,
        contents=cvr_string,
        uploaded_at=datetime.utcnow(),
    )


def clear_cvr_file(jurisdiction: Jurisdiction, delete_cvrs: bool = True):
    if jurisdiction.cvr_file_id:
        File.query.filter_by(id=jurisdiction.cvr_file_id).delete()
    if delete_cvrs:  # pragma: no cover
        # TODO test
        CvrBallot.query.filter_by(jurisdiction_id=jurisdiction.id).delete()


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvr", methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def upload_cvr(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_cvr_upload(request)
    clear_cvr_file(jurisdiction, delete_cvrs=False)
    save_cvr_file(request.files["cvr"], jurisdiction)
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvr", methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_cvr(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify(
        file=serialize_file(jurisdiction.cvr_file),
        processing=serialize_file_processing(jurisdiction.cvr_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvr/csv", methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_cvr_file(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):  # pragma: no cover
    # TODO test
    if not jurisdiction.cvr_file:
        return NotFound()

    return csv_response(jurisdiction.cvr_file.contents, jurisdiction.cvr_file.name)


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvr", methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_cvr(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):  # pragma: no cover
    # TODO test
    clear_cvr_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
