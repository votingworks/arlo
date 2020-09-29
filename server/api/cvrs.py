import uuid
from datetime import datetime
from sqlalchemy.orm.session import Session
from flask import request, jsonify, Request
from werkzeug.exceptions import BadRequest, NotFound
import tempfile
import csv

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


def process_cvr_file(session: Session, jurisdiction: Jurisdiction, file: File):
    assert jurisdiction.cvr_file_id == file.id

    def process():
        cvrs = csv.reader(jurisdiction.cvr_file.contents, delimiter=",")

        election_name = next(cvrs)[0]
        contest_names_row = next(cvrs)
        contest_choices_row = next(cvrs)
        headers_and_party_affiliations_row = next(cvrs)

        with tempfile.TemporaryFile() as temp_file:
            for row in cvrs:
                [
                    cvr_number,
                    tabulator_number,
                    batch_id,
                    record_id,
                    imprinted_id,
                    precinct_portion,
                    ballot_type,
                    *votes,
                ] = row
                temp_file.write(
                    ",".join(
                        [f"{tabulator_number} - {batch_id}", record_id, imprinted_id,]
                    )
                    + "\n"
                )

            temp_file.seek(0)

            connection = session.connection.engine.raw_connection()
            cursor = connection.cursor()
            copy_from = """
                COPY cvr_ballot 
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    DELIMITER ',',
                    HEADER
                );
            """
            cursor.copy_expert(copy_from, temp_file)
            cursor.close()
            connection.commit()
            connection.close()

    process_file(session, file, process)


# Raises if invalid
def validate_cvr_upload(request: Request):
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
    if delete_cvrs:
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
):
    if not jurisdiction.cvr_file:
        return NotFound()

    return csv_response(jurisdiction.cvr_file.contents, jurisdiction.cvr_file.name)


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvr", methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_cvr(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_cvr_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
