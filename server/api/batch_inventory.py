import os
import re
import shutil
import tempfile
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

from server.util.string import strip_optional_string


from ..database import db_session, engine
from . import api
from ..auth.auth_helpers import (
    UserType,
    restrict_access,
    get_loggedin_user,
    get_support_user,
)
from .cvrs import (
    column_value,
    csv_reader_for_cvr,
    get_header_indices,
    read_ess_ballots_file,
    separate_ess_cvr_and_ballots_files,
)
from ..models import *  # pylint: disable=wildcard-import
from ..util.csv_parse import (
    validate_comma_delimited,
    is_filetype_csv_mimetype,
    validate_csv_mimetype,
)
from ..util.file import (
    get_file_upload_url,
    get_standard_file_upload_request_params,
    retrieve_file,
    retrieve_file_to_buffer,
    serialize_file,
    serialize_file_processing,
    timestamp_filename,
    unzip_files,
    validate_csv_or_zip_mimetype,
    validate_zip_mimetype,
    validate_xml_mimetype,
)
from ..util.hart_parse import find_xml, parse_contest_results, find_text_xml
from ..worker.tasks import UserError, background_task, create_background_task
from ..util.csv_download import csv_response, jurisdiction_timestamp_name
from ..util.isoformat import isoformat
from .batch_tallies import construct_contest_choice_csv_headers
from ..activity_log.activity_log import UploadFile, activity_base, record_activity
from ..util.get_json import safe_get_json_dict


TABULATOR_ID = "Tabulator Id"
NAME = "Name"

# (tabulator_id, batch_id)
BatchKey = Tuple[str, str]


def batch_key_to_name(
    batch_key: BatchKey, tabulator_id_to_name: Optional[Dict[str, str]]
) -> str:
    tabulator_id, batch_id = batch_key

    if not tabulator_id:
        return batch_id

    return (
        f"{tabulator_id_to_name[tabulator_id]} - {batch_id}"
        if tabulator_id_to_name
        else f"{tabulator_id} - {batch_id}"
    )


class ElectionResults(TypedDict):
    ballot_count_by_batch: Dict[BatchKey, int]
    ballot_count_by_group: Optional[Dict[str, int]]
    batch_to_counting_group: Optional[Dict[BatchKey, str]]
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
    election_id: str,  # pylint: disable=unused-argument
    jurisdiction_id: str,
    user: Tuple[UserType, str],
    support_user_email: Optional[str],
):
    working_directory = tempfile.mkdtemp()

    def clean_up_file_system():
        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    batch_inventory_data: BatchInventoryData = BatchInventoryData.query.get(
        jurisdiction_id
    )
    contests = list(jurisdiction.contests)
    cvr_file = retrieve_file_to_buffer(
        batch_inventory_data.cvr_file.storage_path, working_directory
    )

    def process_dominion():
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
                    election_id=jurisdiction.election_id,
                    jurisdiction_id=jurisdiction.id,
                    user=user,
                    support_user_email=support_user_email,
                ),
            )

    def process_ess():
        ballot_count_by_batch: Dict[BatchKey, int] = defaultdict(int)
        batch_tallies: Dict[BatchKey, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        def validate_choice_name_and_get_choice_id(choice_name: str) -> Optional[str]:
            choice_id = None
            for choice in contest.choices:
                if choice.name == choice_name:
                    choice_id = choice.id
                    break
                # handle capitalization mismatches for the write in column
                if choice.name.lower() == choice_name.lower() == "write-in":
                    choice_id = choice.id
                    break

            if (
                not choice_id
                and choice_name
                and choice_name != "overvote"
                and choice_name != "undervote"
                # If the user configured a write-in candidate choice when setting up the audit choice_id
                # will be set in the for loop above. If the audit wasn't configured for write-ins we can parse them out.
                and choice_name != "Write-in"
            ):
                raise UserError(f"Unrecognized choice in CVR file: {choice_name}")
            return choice_id

        # ZIP file with multiple CSVs
        if batch_inventory_data.cvr_file.storage_path.endswith(".zip"):
            entry_names = unzip_files(cvr_file, working_directory)
            file_names = [
                entry_name for entry_name in entry_names if entry_name.endswith(".csv")
            ]
            cvr_file.close()

            cvr_and_ballots_files = separate_ess_cvr_and_ballots_files(
                working_directory, file_names
            )
            primary_cvr_file, ballots_files = (
                cvr_and_ballots_files["cvr_file"],
                cvr_and_ballots_files["ballots_files"],
            )

            cvr_number_to_batch = {}
            for ballots_file in ballots_files.values():
                headers, rows = read_ess_ballots_file(ballots_file)
                header_indices = get_header_indices(headers)
                for row_index, row in enumerate(rows):
                    cvr_number = column_value(
                        row,
                        "Cast Vote Record",
                        row_index + 1,
                        header_indices,
                        required=True,
                    )
                    batch_col = column_value(
                        row,
                        "Batch",
                        row_index + 1,
                        header_indices,
                        required=False,
                    )
                    batch_name_col = column_value(
                        row,
                        "Batch Name",
                        row_index + 1,
                        header_indices,
                        required=False,
                    )
                    batch = batch_col if batch_col is not None else batch_name_col
                    if batch is None:
                        raise UserError(
                            "Missing Batch and Batch Name columns from CSV, at least one must be defined."
                        )
                    cvr_number_to_batch[cvr_number] = batch

            validate_comma_delimited(primary_cvr_file)
            cvr_csv = csv.reader(primary_cvr_file, delimiter=",")
            headers = next(cvr_csv)
            header_indices = get_header_indices(headers)

            contest_names = [contest.name for contest in contests]
            missing_contest_names = set(contest_names) - set(headers)
            if len(missing_contest_names) != 0:
                raise UserError(
                    f"CVR file is missing contest names: {', '.join(missing_contest_names)}"
                )

            for row_index, row in enumerate(cvr_csv):
                cvr_number = column_value(
                    row,
                    "Cast Vote Record",
                    row_index + 1,
                    header_indices,
                    required=True,
                )

                if cvr_number not in cvr_number_to_batch:
                    raise UserError(
                        f"Unable to find batch for CVR number {cvr_number} in ballots files"
                    )
                batch = cvr_number_to_batch[cvr_number]
                batch_key: BatchKey = ("", batch)
                ballot_count_by_batch[batch_key] += 1

                for contest in contests:
                    choice_name = column_value(
                        row,
                        contest.name,
                        row_index + 1,
                        header_indices,
                        required=False,
                    )
                    choice_id = validate_choice_name_and_get_choice_id(choice_name)

                    if choice_id:
                        batch_tallies[batch_key][choice_id] += 1

        # Single CSV file
        else:
            cvrs = csv_reader_for_cvr(cvr_file)
            headers = next(cvrs)
            header_indices = get_header_indices(headers)
            for row_index, row in enumerate(cvrs):
                for contest in contests:
                    batch_col = column_value(
                        row,
                        "Batch",
                        row_index + 1,
                        header_indices,
                        required=False,
                    )
                    batch_name_col = column_value(
                        row,
                        "Batch Name",
                        row_index + 1,
                        header_indices,
                        required=False,
                    )
                    batch = batch_col if batch_col is not None else batch_name_col
                    if batch is None:
                        raise UserError(
                            "Missing Batch and Batch Name columns from CSV, at least one must be defined."
                        )
                    choice_name = column_value(
                        row,
                        contest.name,
                        row_index + 1,
                        header_indices,
                        required=False,
                    )

                    batch_key: BatchKey = ("", batch)
                    choice_id = validate_choice_name_and_get_choice_id(choice_name)

                    ballot_count_by_batch[batch_key] += 1
                    if choice_id:
                        batch_tallies[batch_key][choice_id] += 1

        # Set explicit zeros for choices with zero votes in a batch to avoid KeyErrors when
        # generating files
        for batch_key in ballot_count_by_batch.keys():
            if batch_key not in batch_tallies:
                batch_tallies[batch_key] = defaultdict(int)
        for tallies in batch_tallies.values():
            for contest in contests:
                for choice in contest.choices:
                    if choice.id not in tallies:
                        tallies[choice.id] = 0

        election_results: ElectionResults = dict(
            ballot_count_by_batch=dict_to_items_list(ballot_count_by_batch),
            ballot_count_by_group=None,
            batch_to_counting_group=None,
            batch_tallies=dict_to_items_list(batch_tallies),
        )
        batch_inventory_data.election_results = election_results

    def process_hart():
        ballot_count_by_batch: Dict[BatchKey, int] = defaultdict(int)
        batch_tallies: Dict[BatchKey, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        def validate_choice_name_and_get_choice_id(choice_name: str) -> Optional[str]:
            choice_id = None
            for choice in contest.choices:
                if choice.name == choice_name:
                    choice_id = choice.id
                    break
                # handle capitalization mismatches for the write in column
                if choice.name.lower() == choice_name.lower() == "write-in":
                    choice_id = choice.id
                    break
            if (
                not choice_id
                and choice_name
                # If the user configured a write-in candidate choice when setting up the audit choice_id
                # will be set in the for loop above. If the audit wasn't configured for write-ins we can parse them out.
                and choice_name.lower() != "write-in"
            ):
                raise UserError(f"Unrecognized choice in CVR file: {choice_name}")
            return choice_id

        # cvr_file is a ZIP file with multiple XMLs
        zip_entry_names = unzip_files(cvr_file, working_directory)
        cvr_file_names = [
            entry_name
            for entry_name in zip_entry_names
            if entry_name.lower().endswith(".xml")
        ]
        cvr_file.close()

        for cvr_file_name in cvr_file_names:
            cvr_xml = ElementTree.parse(os.path.join(working_directory, cvr_file_name))
            batch_number = find_text_xml(cvr_xml, "BatchNumber")
            precinct_name = find_text_xml(find_xml(cvr_xml, "PrecinctSplit"), "Name")
            batch_key_value = (
                batch_number if batch_number is not None else precinct_name
            )
            if batch_key_value is None:
                raise UserError(
                    "Could not find batch number or precinct name in CVR file."
                )
            batch_key: BatchKey = (
                "",
                batch_key_value,
            )  # Tabulator ID is not present in Hart CVRs

            ballot_count_by_batch[batch_key] += 1
            contest_results = parse_contest_results(cvr_xml)
            for contest in contests:
                choices = contest_results.get(contest.name, set())
                for choice_name in choices:
                    choice_id = validate_choice_name_and_get_choice_id(choice_name)
                    if choice_id is not None:
                        batch_tallies[batch_key][choice_id] += 1

        # Set explicit zeros for choices with zero votes in a batch to avoid KeyErrors when
        # generating files and to make sure every batch is included even if it has no votes for the contest(s)
        for batch_key in ballot_count_by_batch.keys():
            if batch_key not in batch_tallies:
                batch_tallies[batch_key] = defaultdict(int)
        for tallies in batch_tallies.values():
            for contest in contests:
                for choice in contest.choices:
                    if choice.id not in tallies:
                        tallies[choice.id] = 0

        election_results: ElectionResults = dict(
            ballot_count_by_batch=dict_to_items_list(ballot_count_by_batch),
            ballot_count_by_group=None,
            batch_to_counting_group=None,
            batch_tallies=dict_to_items_list(batch_tallies),
        )
        batch_inventory_data.election_results = election_results

    def process():
        if batch_inventory_data.system_type == CvrFileType.DOMINION:
            process_dominion()
        elif batch_inventory_data.system_type == CvrFileType.ESS:
            process_ess()
        elif batch_inventory_data.system_type == CvrFileType.HART:
            process_hart()
        else:
            raise Exception(
                f"Unrecognized system type: {batch_inventory_data.system_type}"
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
        clean_up_file_system()


TABULATOR_STATUS_PARSE_ERROR = (
    "We could not parse this file. Please make sure you upload either the plain XML version or Excel version of the tabulator status report."
    ' The file name should end in ".xml".'
)


@background_task
def process_batch_inventory_tabulator_status_file(
    election_id: str,  # pylint: disable=unused-argument
    jurisdiction_id: str,
    user: Tuple[UserType, str],
    support_user_email: Optional[str],
):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction_id)

    def get_tabulator_id_to_name_dict_for_excel_file(
        cvr_xml: ElementTree.ElementTree,
    ):
        namespaces = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
        # List of all rows in the table
        rows = cvr_xml.findall(
            ".//ss:Worksheet[@ss:Name='Tabulator Status']/ss:Table/ss:Row",
            namespaces,
        )
        # List of all rows and text content of each cell in the row. eg.
        # [ ...
        #   ["Tabulator Id", "Name",          "Load Status", "Total Ballots Cast"],
        #   ["TABULATOR1",   "Tabulator One", "1",           "123"],
        #   ["TABULATOR2",   "Tabulator Two", "1",           "456"],
        #   ...
        # ]
        rows_with_cell_text = [
            [
                strip_optional_string(data_element.text)
                for data_element in row.findall(
                    "ss:Cell/ss:Data[@ss:Type='String']", namespaces
                )
            ]
            for row in rows
        ]

        # Get the column headers row so we know at which indices to access "Tabulator Id" and "Name" later
        column_header_row_index = next(
            (
                i
                for i, row_cells in enumerate(rows_with_cell_text)
                if TABULATOR_ID in row_cells
            ),
            -1,
        )

        # Validate column header row was found
        if column_header_row_index == -1:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR)

        # Validate we have at least 1 row of tabulator data after the column headers
        if column_header_row_index == len(rows_with_cell_text) - 1:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR)

        column_headers_row = rows_with_cell_text[column_header_row_index]

        # Get the position of "Tabulator Id" and "Name" values in the list of cells for a single row
        tabulator_id_index = column_headers_row.index(TABULATOR_ID)
        tabulator_name_index = column_headers_row.index(NAME)

        return {
            tabulator_data_row[tabulator_id_index]: tabulator_data_row[
                tabulator_name_index
            ]
            for tabulator_data_row in rows_with_cell_text[column_header_row_index + 1 :]
        }

    def get_tabulator_id_to_name_dict_for_plain_xml_file(
        cvr_xml: ElementTree.ElementTree,
    ) -> Dict[Optional[str], Optional[str]]:
        tabulators = cvr_xml.findall("tabulators/tb")
        if len(tabulators) == 0:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR)

        return {tabulator.get("tid"): tabulator.get("name") for tabulator in tabulators}

    def process():
        file = retrieve_file(batch_inventory_data.tabulator_status_file.storage_path)
        try:
            cvr_xml = ElementTree.parse(file)
        except Exception as error:
            raise UserError(TABULATOR_STATUS_PARSE_ERROR) from error

        root = cvr_xml.getroot()
        is_ms_excel_file = re.match(
            r"\{urn:schemas-microsoft-com:office:spreadsheet\}", root.tag
        )
        tabulator_id_to_name = (
            get_tabulator_id_to_name_dict_for_excel_file(cvr_xml)
            if is_ms_excel_file
            else get_tabulator_id_to_name_dict_for_plain_xml_file(cvr_xml)
        )

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
    system_type = safe_get_json_dict(request)["systemType"]
    if system_type is None:
        raise BadRequest("Missing systemType param")
    if system_type not in [CvrFileType.DOMINION, CvrFileType.ESS, CvrFileType.HART]:
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
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr/upload-url",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def start_upload_for_batch_inventory_cvr(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    file_type = request.args.get("fileType")
    if file_type is None:
        raise BadRequest("Missing expected query parameter: fileType")

    is_csv = is_filetype_csv_mimetype(file_type)

    storage_path_prefix = f"audits/{election.id}/jurisdictions/{jurisdiction.id}"
    filename = timestamp_filename("batch-inventory-cvrs", "csv" if is_csv else "zip")

    return jsonify(get_file_upload_url(storage_path_prefix, filename, file_type))


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/cvr/upload-complete",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def complete_upload_for_batch_inventory_cvr(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    if len(list(jurisdiction.contests)) == 0:
        raise Conflict("Jurisdiction does not have any contests assigned.")

    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.system_type:
        raise Conflict("Must select system type before uploading CVR file.")

    (storage_path, filename, file_type) = get_standard_file_upload_request_params(
        request
    )

    if batch_inventory_data.system_type == CvrFileType.DOMINION:
        validate_csv_mimetype(file_type)
    elif batch_inventory_data.system_type == CvrFileType.ESS:
        validate_csv_or_zip_mimetype(file_type)
    elif batch_inventory_data.system_type == CvrFileType.HART:
        validate_zip_mimetype(file_type)
    else:
        raise Conflict(
            f"Batch Inventory CVR uploads not supported for cvr file type: {batch_inventory_data.system_type}"
        )

    batch_inventory_data.cvr_file = File(
        id=str(uuid.uuid4()),
        name=filename,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    batch_inventory_data.cvr_file.task = create_background_task(
        process_batch_inventory_cvr_file,
        dict(
            election_id=election.id,
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.cvr_file:
        raise NotFound()

    return csv_response(
        retrieve_file(batch_inventory_data.cvr_file.storage_path),
        batch_inventory_data.cvr_file.name,
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status/upload-url",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def start_upload_for_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction
):

    file_type = request.args.get("fileType")
    if file_type is None:
        raise BadRequest("Missing expected query parameter: fileType")

    storage_path_prefix = f"audits/{election.id}/jurisdictions/{jurisdiction.id}"
    filename = timestamp_filename("batch-inventory-tabulator-status", "xml")

    return jsonify(get_file_upload_url(storage_path_prefix, filename, file_type))


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch-inventory/tabulator-status/upload-complete",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def complete_upload_for_batch_inventory_tabulator_status(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):

    batch_inventory_data = BatchInventoryData.query.get(jurisdiction.id)
    if not batch_inventory_data or not batch_inventory_data.cvr_file_id:
        raise Conflict("Must upload CVR file before uploading tabulator status file.")

    if batch_inventory_data.cvr_file.is_processing():
        raise Conflict(
            "Cannot update tabulator status while CVR file is being processed."
        )

    (storage_path, filename, file_type) = get_standard_file_upload_request_params(
        request
    )
    validate_xml_mimetype(file_type)

    batch_inventory_data.tabulator_status_file = File(
        id=str(uuid.uuid4()),
        name=filename,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    batch_inventory_data.tabulator_status_file.task = create_background_task(
        process_batch_inventory_tabulator_status_file,
        dict(
            election_id=election.id,
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
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
    for group_name, ballot_count in (
        election_results["ballot_count_by_group"] or {}
    ).items():
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
            [
                batch_name,
                ballot_count,
                "",
            ]
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

    # We originally didn't have a batch_to_counting_group key at all, so we protect against the key
    # not existing by using .get for backwards compatibility
    batch_to_counting_group = items_list_to_dict(
        election_results.get("batch_to_counting_group", None) or []
    )
    should_include_container_column = len(batch_to_counting_group) > 0

    if should_include_container_column:
        ballot_manifest.writerow(["Container", "Batch Name", "Number of Ballots"])
    else:
        ballot_manifest.writerow(["Batch Name", "Number of Ballots"])

    for batch_key, ballot_count in items_list_to_dict(
        election_results["ballot_count_by_batch"]
    ).items():
        batch_name = batch_key_to_name(
            batch_key, batch_inventory_data.tabulator_id_to_name
        )
        if should_include_container_column:
            counting_group = batch_to_counting_group.get(batch_key)
            ballot_manifest.writerow([counting_group, batch_name, ballot_count])
        else:
            ballot_manifest.writerow([batch_name, ballot_count])

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
