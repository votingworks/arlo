from collections import defaultdict
import csv
from datetime import datetime, timezone
import io
from typing import TypedDict, Dict, Tuple, Optional
import uuid
from xml.etree import ElementTree
from flask import request, jsonify, session
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy.orm import Session


from ..database import db_session, engine
from . import api
from ..auth.auth_helpers import (
    UserType,
    restrict_access,
    get_loggedin_user,
    get_support_user,
)
from .cvrs import column_value, csv_reader_for_cvr, get_header_indices
from ..models import *  # pylint: disable=wildcard-import
from ..util.csv_parse import (
    does_file_have_csv_mimetype,
    does_file_have_zip_mimetype,
    INVALID_CSV_ERROR,
)
from ..util.file import (
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    store_file,
    timestamp_filename,
)
from ..worker.tasks import UserError, background_task, create_background_task
from ..util.csv_download import csv_response, jurisdiction_timestamp_name
from ..util.isoformat import isoformat
from .batch_tallies import construct_contest_choice_csv_headers
from ..activity_log.activity_log import UploadFile, activity_base, record_activity

# (tabulator_id, batch_id)
BatchKey = Tuple[str, str]


def batch_key_to_name(batch_key: BatchKey, tabulator_id_to_name: Dict[str, str]) -> str:
    tabulator_id, batch_id = batch_key
    return f"{tabulator_id_to_name[tabulator_id]} - {batch_id}"


class ElectionResults(TypedDict):
    ballot_count_by_batch: Dict[BatchKey, int]
    ballot_count_by_group: Dict[str, int]
    batch_to_counting_group: Dict[BatchKey, str]
    # { batch_key: { choice_id: count } }
    batch_tallies: Dict[BatchKey, Dict[str, int]]


def dict_to_items_list(dictionary):
    return [dict(key=key, value=value) for key, value in dictionary.items()]


def items_list_to_dict(items):
    return {
        (tuple(item["key"]) if isinstance(item["key"], list) else item["key"]): item[
            "value"
        ]
        for item in items
    }


@background_task
def process_batch_inventory_cvr_file(
    jurisdiction_id: str, user: Tuple[UserType, str], support_user_email: Optional[str],
):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_id)

    def process():
        contests = list(jurisdiction.contests)

        cvr_file = retrieve_file(batch_inventory_data.cvr_file.storage_path)
        cvrs = csv_reader_for_cvr(cvr_file)

        # Parse out all the initial metadata
        _election_name = next(cvrs)[0]
        contests_row = [" ".join(contest.splitlines()) for contest in next(cvrs)]
        contest_choices_row = next(cvrs)
        headers_and_affiliations = next(cvrs)

        expected_contest_headers = [
            f"{contest.name} (Vote For={contest.votes_allowed})" for contest in contests
        ]

        missing_contest_headers = [
            expected_contest_header
            for expected_contest_header in expected_contest_headers
            if expected_contest_header not in contests_row
        ]
        if len(missing_contest_headers) > 0:
            raise UserError(
                f"Could not find contests in CVR file: {', '.join(missing_contest_headers)}."
            )

        choice_indices = {
            (
                contests[expected_contest_headers.index(contest_header)].name,
                choice_name,
            ): index
            for index, (contest_header, choice_name) in enumerate(
                zip(contests_row, contest_choices_row)
            )
            if contest_header in expected_contest_headers
        }

        missing_choices = set(
            (contest.name, choice.name)
            for contest in contests
            for choice in contest.choices
        ) - set(choice_indices.keys())
        if len(missing_choices) > 0:
            missing_choices_strings = [
                f"{choice_name} for contest {contest_name}"
                for contest_name, choice_name in missing_choices
            ]
            raise UserError(
                f"Could not find contest choices in CVR file: {', '.join(missing_choices_strings)}."
            )

        header_indices = get_header_indices(headers_and_affiliations)

        ballot_count_by_group: Dict[str, int] = defaultdict(int)
        ballot_count_by_batch: Dict[BatchKey, int] = defaultdict(int)
        batch_to_counting_group: Dict[BatchKey, str] = {}
        batch_tallies: Dict[BatchKey, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        def parse_vote(vote: str):
            return int(vote if vote != "" else 0)

        for row_index, row in enumerate(cvrs):
            cvr_number = column_value(
                row,
                "CvrNumber",
                row_index + 1,
                header_indices,
                remove_leading_equal_sign=True,
            )
            tabulator_number = column_value(
                row,
                "TabulatorNum",
                cvr_number,
                header_indices,
                remove_leading_equal_sign=True,
            )
            batch_id = column_value(
                row,
                "BatchId",
                cvr_number,
                header_indices,
                remove_leading_equal_sign=True,
            )
            counting_group = column_value(
                row, "CountingGroup", cvr_number, header_indices
            )

            batch_key = (tabulator_number, batch_id)

            ballot_count_by_batch[batch_key] += 1
            ballot_count_by_group[counting_group] += 1
            batch_to_counting_group[batch_key] = counting_group

            for contest in contests:
                contest_choice_votes: Dict[str, int] = {
                    choice.id: parse_vote(
                        column_value(
                            row,
                            (contest.name, choice.name),
                            cvr_number,
                            choice_indices,
                            required=False,
                            header_readable_string_override=f"{choice.name} for contest {contest.name}",
                        )
                    )
                    for choice in contest.choices
                }

                # Skip overvotes
                if sum(contest_choice_votes.values()) > contest.votes_allowed:
                    continue

                for choice_id, vote in contest_choice_votes.items():
                    batch_tallies[batch_key][choice_id] += vote

        election_results: ElectionResults = dict(
            ballot_count_by_batch=dict_to_items_list(ballot_count_by_batch),
            ballot_count_by_group=dict(ballot_count_by_group),
            batch_to_counting_group=dict_to_items_list(batch_to_counting_group),
            batch_tallies=dict_to_items_list(batch_tallies),
        )
        batch_inventory_data.election_results = election_results

        # If tabulator status file already uploaded, try reprocessing it, since it
        # validates tabulator names against the CVR file.
        if batch_inventory_data.tabulator_status_file:
            batch_inventory_data.tabulator_id_to_name = None
            batch_inventory_data.tabulator_status_file.task = create_background_task(
                process_batch_inventory_tabulator_status_file,
                dict(
                    jurisdiction_id=jurisdiction.id,
                    user=user,
                    support_user_email=support_user_email,
                ),
            )

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
                timestamp=batch_inventory_data.cvr_file.uploaded_at,
                base=base,
                jurisdiction_id=jurisdiction.id,
                jurisdiction_name=jurisdiction.name,
                file_type="batch_inventory_cvrs",
                error=error,
            ),
            session,
        )
        session.commit()


TABULATOR_STATUS_PARSE_ERROR = (
    "We could not parse this file. Please make sure you upload the plain XML version of the tabulator status report."
    ' The file name should end in ".xml" and should not contain the words "To Excel".'
)


@background_task
def process_batch_inventory_tabulator_status_file(
    jurisdiction_id: str, user: Tuple[UserType, str], support_user_email: Optional[str],
):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_id)

    def process():
        file = retrieve_file(batch_inventory_data.tabulator_status_file.storage_path)
        try:
            cvr_xml = ElementTree.parse(file)
        except Exception as error:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR) from error

        tabulators = cvr_xml.findall("tabulators/tb")
        if len(tabulators) == 0:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR)
        tabulator_id_to_name = {
            tabulator.get("tid"): tabulator.get("name") for tabulator in tabulators
        }

        ballot_count_by_batch = items_list_to_dict(
            batch_inventory_data.election_results["ballot_count_by_batch"]
        )
        cvr_tabulator_ids = {
            tabulator_id for (tabulator_id, _) in ballot_count_by_batch.keys()
        }
        missing_tabulators = set(cvr_tabulator_ids) - set(tabulator_id_to_name.keys())
        if len(missing_tabulators) > 0:
            raise UserError(
                "Could not find some tabulators from CVR file in Tabulator Status file."
                f" Missing tabulator IDs: {', '.join(missing_tabulators)}."
            )

        batch_inventory_data.tabulator_id_to_name = tabulator_id_to_name

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
                timestamp=batch_inventory_data.tabulator_status_file.uploaded_at,
                base=base,
                jurisdiction_id=jurisdiction.id,
                jurisdiction_name=jurisdiction.name,
                file_type="batch_inventory_tabulator_status",
                error=error,
            ),
            session,
        )
        session.commit()


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/system-type",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def set_batch_inventory_system_type(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    system_type = request.get_json()["systemType"]
    if system_type is None:
        raise BadRequest("Missing systemType param")
    if system_type not in [CvrFileType.DOMINION, CvrFileType.ESS]:
        raise BadRequest(f"Unrecognized systemType param: {system_type}")

    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data:
        batch_inventory_data = BatchInventoryData(jurisdiction_id=jurisdiction.id)
        db_session.add(batch_inventory_data)

    batch_inventory_data.system_type = system_type

    # Clear dependent data
    if batch_inventory_data.cvr_file_id:
        File.query.filter_by(id=batch_inventory_data.cvr_file_id).delete()
    if batch_inventory_data.tabulator_status_file_id:
        File.query.filter_by(id=batch_inventory_data.tabulator_status_file_id).delete()
    batch_inventory_data.election_results = None
    clear_sign_off(batch_inventory_data)

    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/system-type",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_batch_inventory_system_type(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    return jsonify(
        dict(
            systemType=(
                batch_inventory_data.system_type if batch_inventory_data else None
            )
        )
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def upload_batch_inventory_cvr(election: Election, jurisdiction: Jurisdiction):
    if len(list(jurisdiction.contests)) == 0:
        raise Conflict("Jurisdiction does not have any contests assigned.")

    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.system_type:
        raise Conflict("Must select system type before uploading CVR file.")

    file = request.files["cvr"]
    file_type = (
        "csv"
        if does_file_have_csv_mimetype(file)
        else "zip"
        if does_file_have_zip_mimetype(file)
        else "other"
    )

    if batch_inventory_data.system_type == CvrFileType.DOMINION and file_type != "csv":
        raise BadRequest(INVALID_CSV_ERROR)
    elif (
        batch_inventory_data.system_type == CvrFileType.ESS
        and file_type != "csv"
        and file_type != "zip"
    ):
        raise BadRequest("Please submit a valid CSV or ZIP file.")

    assert file_type != "other"

    file_name = file.filename
    storage_path = store_file(
        file.stream,
        f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
        + timestamp_filename("batch-inventory-cvrs", file_type),
    )

    batch_inventory_data.cvr_file = File(
        id=str(uuid.uuid4()),
        name=file_name,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    batch_inventory_data.cvr_file.task = create_background_task(
        process_batch_inventory_cvr_file,
        dict(
            jurisdiction_id=jurisdiction.id,
            user=get_loggedin_user(session),
            support_user_email=get_support_user(session),
        ),
    )
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_batch_inventory_cvr(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data:
        return jsonify(file=None, processing=None)
    return jsonify(
        file=serialize_file(batch_inventory_data.cvr_file),
        processing=serialize_file_processing(batch_inventory_data.cvr_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_batch_inventory_cvr(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)

    if batch_inventory_data.cvr_file_id:
        File.query.filter_by(id=batch_inventory_data.cvr_file_id).delete()
        batch_inventory_data.election_results = None

    # Undo sign off, since it's no longer valid
    clear_sign_off(batch_inventory_data)

    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr/file",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def download_batch_inventory_cvr(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.cvr_file:
        raise NotFound()

    return csv_response(
        retrieve_file(batch_inventory_data.cvr_file.storage_path),
        batch_inventory_data.cvr_file.name,
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def upload_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.cvr_file_id:
        raise Conflict("Must upload CVR file before uploading tabulator status file.")

    file_name = request.files["tabulatorStatus"].filename
    storage_path = store_file(
        request.files["tabulatorStatus"].stream,
        f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
        + timestamp_filename("batch-inventory-tabulator-status", "xml"),
    )

    batch_inventory_data.tabulator_status_file = File(
        id=str(uuid.uuid4()),
        name=file_name,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    batch_inventory_data.tabulator_status_file.task = create_background_task(
        process_batch_inventory_tabulator_status_file,
        dict(
            jurisdiction_id=jurisdiction.id,
            user=get_loggedin_user(session),
            support_user_email=get_support_user(session),
        ),
    )
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data:
        return jsonify(file=None, processing=None)
    return jsonify(
        file=serialize_file(batch_inventory_data.tabulator_status_file),
        processing=serialize_file_processing(
            batch_inventory_data.tabulator_status_file
        ),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)

    if batch_inventory_data.tabulator_status_file_id:
        File.query.filter_by(id=batch_inventory_data.tabulator_status_file_id).delete()
        batch_inventory_data.tabulator_id_to_name = None

    # Undo sign off, since it's no longer valid
    clear_sign_off(batch_inventory_data)

    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status/file",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def download_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.tabulator_status_file:
        raise NotFound()

    return csv_response(
        retrieve_file(batch_inventory_data.tabulator_status_file.storage_path),
        batch_inventory_data.tabulator_status_file.name,
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/worksheet",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def download_batch_inventory_worksheet(election: Election, jurisdiction: Jurisdiction):
    batch_inventory_data = get_or_404(BatchInventoryData, jurisdiction.id)
    election_results: ElectionResults = batch_inventory_data.election_results

    csv_io = io.StringIO()
    worksheet = csv.writer(csv_io)

    worksheet.writerow(["Batch Inventory Worksheet"])
    worksheet.writerow([])

    worksheet.writerow(["Section 1: Check Ballot Groups"])
    instructions = [
        "1. Compare the CVR Ballot Count for each ballot group to your voter check-in data.",
        "2. Ensure that the numbers reconcile. If there is a large discrepancy contact your SOS liaison.",
    ]
    for instruction in instructions:
        worksheet.writerow([instruction])
    worksheet.writerow([])

    worksheet.writerow(["Ballot Group", "CVR Ballot Count", "Checked? (Type Yes/No)"])
    for group_name, ballot_count in election_results["ballot_count_by_group"].items():
        worksheet.writerow([group_name, ballot_count, ""])
    worksheet.writerow([])

    worksheet.writerow(["Section 2: Check Batches"])
    instructions = [
        "1. Locate each batch in storage.",
        "2. Confirm the CVR Ballot Count is correct using associated documentation. Do NOT count the ballots. If there is a large discrepancy contact your SOS liaison.",
        "3. Make sure there are no batches missing from this worksheet.",
    ]
    for instruction in instructions:
        worksheet.writerow([instruction])
    worksheet.writerow([])

    worksheet.writerow(["Batch", "CVR Ballot Count", "Checked? (Type Yes/No)"])
    for batch_key, ballot_count in items_list_to_dict(
        election_results["ballot_count_by_batch"]
    ).items():
        batch_name = batch_key_to_name(
            batch_key, batch_inventory_data.tabulator_id_to_name
        )
        worksheet.writerow(
            [batch_name, ballot_count, "",]
        )

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"batch-inventory-worksheet-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/sign-off",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def batch_inventory_sign_off_status(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    return jsonify(
        dict(
            signedOffAt=batch_inventory_data
            and isoformat(batch_inventory_data.signed_off_at)
        )
    )


def clear_sign_off(batch_inventory_data: BatchInventoryData):
    batch_inventory_data.signed_off_at = None
    batch_inventory_data.sign_off_user_id = None


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/sign-off",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def sign_off_batch_inventory(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = get_or_404(BatchInventoryData, jurisdiction.id)
    batch_inventory_data.signed_off_at = datetime.now(timezone.utc)
    _, user_email = get_loggedin_user(session)
    user_id = User.query.filter_by(email=user_email).one().id
    batch_inventory_data.sign_off_user_id = user_id
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/sign-off",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def undo_sign_off_batch_inventory(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    batch_inventory_data = get_or_404(BatchInventoryData, jurisdiction.id)
    clear_sign_off(batch_inventory_data)
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/ballot-manifest",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def download_batch_inventory_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction
):
    batch_inventory_data = get_or_404(BatchInventoryData, jurisdiction.id)
    election_results: ElectionResults = batch_inventory_data.election_results

    csv_io = io.StringIO()
    ballot_manifest = csv.writer(csv_io)

    ballot_manifest.writerow(["Container", "Batch Name", "Number of Ballots"])

    # We originally didn't have counting group stored, so we make this
    # optional for backwards compatibility
    batch_to_counting_group = items_list_to_dict(
        election_results.get("batch_to_counting_group", [])
    )

    for batch_key, ballot_count in items_list_to_dict(
        election_results["ballot_count_by_batch"]
    ).items():
        batch_name = batch_key_to_name(
            batch_key, batch_inventory_data.tabulator_id_to_name
        )
        counting_group = batch_to_counting_group.get(batch_key)
        ballot_manifest.writerow([counting_group, batch_name, ballot_count])

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"ballot-manifest-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/batch-tallies",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def download_batch_inventory_batch_tallies(
    election: Election, jurisdiction: Jurisdiction
):
    batch_inventory_data = get_or_404(BatchInventoryData, jurisdiction.id)
    election_results: ElectionResults = batch_inventory_data.election_results

    contest_choice_csv_headers = construct_contest_choice_csv_headers(
        election, jurisdiction
    )

    csv_io = io.StringIO()
    batch_tallies = csv.writer(csv_io)

    batch_tallies.writerow(["Batch Name", *contest_choice_csv_headers.values()])
    for batch_key, tallies in items_list_to_dict(
        election_results["batch_tallies"]
    ).items():
        batch_name = batch_key_to_name(
            batch_key, batch_inventory_data.tabulator_id_to_name
        )
        batch_tallies.writerow(
            [batch_name]
            + [tallies[choice_id] for _, choice_id in contest_choice_csv_headers.keys()]
        )

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"candidate-totals-by-batch-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )
