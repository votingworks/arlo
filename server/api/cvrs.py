import uuid
import tempfile
import csv
import itertools
from typing import (
    IO,
    BinaryIO,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    TextIO,
    Tuple,
    TypedDict,
    cast as typing_cast,
)
from collections import defaultdict
import re
import difflib
import ast
from datetime import datetime
from flask import request, jsonify, Request, session
from werkzeug.exceptions import BadRequest, NotFound, Conflict
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from . import api
from ..database import db_session, engine as db_engine
from ..models import *  # pylint: disable=wildcard-import
from . import contests
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
    unzip_files,
    zip_files,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import (
    CSVIterator,
    decode_csv,
    validate_comma_delimited,
    validate_csv_mimetype,
    validate_not_empty,
)
from ..audit_math.suite import HybridPair
from ..activity_log.activity_log import UploadFile, activity_base, record_activity


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
    for jurisdiction in contest.jurisdictions:
        contests_metadata = cvr_contests_metadata(jurisdiction)
        if contests_metadata is None:
            raise UserError("Some jurisdictions haven't uploaded their CVRs yet.")

        if contest.name not in contests_metadata:
            raise UserError(
                f"Couldn't find contest {contest.name} in the CVR for jurisdiction {jurisdiction.name}"
            )

        # In hybrid audits, we need to check that the choice names match those
        # entered by the audit admin.
        if contest.election.audit_type == AuditType.HYBRID:
            contest_choice_names = {choice.name for choice in contest.choices}
            cvr_choice_names = set(contests_metadata[contest.name]["choices"].keys())
            if not cvr_choice_names.issubset(contest_choice_names):
                raise UserError(
                    f"CVR choice names don't match for contest {contest.name}:\n"
                    f"{jurisdiction.name}: {', '.join(sorted(cvr_choice_names))}\n"
                    f"Contest settings: {', '.join(sorted(contest_choice_names))}"
                )


def are_uploaded_cvrs_valid(contest: Contest):
    try:
        validate_uploaded_cvrs(contest)
        return True
    except UserError:
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
    if not are_uploaded_cvrs_valid(contest) or len(list(contest.jurisdictions)) == 0:
        return

    first_jurisdiction_metadata = cvr_contests_metadata(list(contest.jurisdictions)[0])
    assert first_jurisdiction_metadata is not None
    contest.votes_allowed = first_jurisdiction_metadata[contest.name]["votes_allowed"]

    # ES&S/Hart CVRs may only have some of the contest choices in each
    # jurisdiction, so we union choice names across jurisdictions, adding up the
    # votes. In Dominion/ClearBallot CVRs, this should have no impact, since the
    # choice names will be the same across jurisdictions. This is safe to do
    # because contest choice names are set by the state, so the same choice
    # should have the same name across jurisdictions.
    choices: Dict[str, int] = defaultdict(lambda: 0)
    for jurisdiction in contest.jurisdictions:
        metadata = cvr_contests_metadata(jurisdiction)
        assert metadata is not None
        for choice_name, choice_metadata in metadata[contest.name]["choices"].items():
            choices[choice_name] += choice_metadata["num_votes"]

    contest.choices = [
        ContestChoice(
            id=str(uuid.uuid4()),
            contest_id=contest.id,
            name=choice_name,
            num_votes=num_votes,
        )
        for choice_name, num_votes in choices.items()
    ]


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


def csv_reader_for_cvr(cvr_file: BinaryIO) -> CSVIterator:
    validate_not_empty(cvr_file)
    text_file = decode_csv(cvr_file)
    validate_comma_delimited(text_file)
    return csv.reader(text_file, delimiter=",")


def get_header_indices(headers_row: List[str]) -> Dict[str, int]:
    return {header: i for i, header in enumerate(headers_row)}


def column_value(
    row: List[str],
    header: str,
    row_number: int,
    header_indices: Dict[str, int],
    required: bool = True,
):
    index = header_indices.get(header)
    if index is None:
        if required:
            raise UserError(f"Missing required column {header}")
        return None
    value = row[index] if index < len(row) else None
    if required and (value is None or value == ""):
        raise UserError(f"Missing required column {header} in row {row_number}.")
    return value


def parse_clearballot_cvrs(
    jurisdiction: Jurisdiction,
) -> Tuple[CVR_CONTESTS_METADATA, Iterable[CvrBallot]]:
    cvr_file = retrieve_file(jurisdiction.cvr_file.storage_path)
    cvrs = csv_reader_for_cvr(cvr_file)
    headers = next(cvrs)
    first_contest_column = next(
        i for i, header in enumerate(headers) if header.startswith("Choice_")
    )

    # Parse out metadata about the contests to store - we'll later use this
    # to populate the Contest object.
    #
    # Contest headers look like this:
    # "Choice_1_1:Presidential Primary:Vote For 1:Joe Schmo:Non-Partisan"
    # We want to parse: contest_name="Presidential Primary", votes_allowed=1, choice_name="Joe Schmo"
    contests_metadata: CVR_CONTESTS_METADATA = defaultdict(
        lambda: dict(choices=dict(), votes_allowed=0, total_ballots_cast=0)
    )
    for column, header in enumerate(headers[first_contest_column:]):
        match = re.match(r"^.*:(.*):Vote For (\d+):(.*):.*$", header)
        if not match:
            raise UserError(f"Invalid contest header: {header}")
        [contest_name, votes_allowed, choice_name] = match.groups()
        contests_metadata[contest_name]["votes_allowed"] = int(votes_allowed)
        contests_metadata[contest_name]["choices"][choice_name] = dict(
            # Store the column index of this contest choice so we can parse
            # interpretations later
            column=column,
            num_votes=0,  # Will be counted while parsing rows
        )
        # Will be counted while parsing rows
        contests_metadata[contest_name]["total_ballots_cast"] = 0

    batches_by_key = {
        (batch.tabulator, batch.name): batch for batch in jurisdiction.batches
    }
    header_indices = get_header_indices(headers)

    def parse_cvr_rows() -> Iterable[CvrBallot]:
        for row_index, row in enumerate(cvrs):
            row_number = column_value(row, "RowNumber", row_index + 1, header_indices)
            box_id = column_value(row, "BoxID", row_number, header_indices)
            box_position = column_value(row, "BoxPosition", row_number, header_indices)
            ballot_id = column_value(row, "BallotID", row_number, header_indices)
            scan_computer_name = column_value(
                row, "ScanComputerName", row_number, header_indices
            )
            interpretations = row[first_contest_column:]

            db_batch = batches_by_key.get((scan_computer_name, box_id))
            if db_batch:
                yield CvrBallot(
                    batch=db_batch,
                    record_id=int(box_position),
                    imprinted_id=ballot_id,
                    interpretations=",".join(interpretations),
                )
            else:
                close_matches = difflib.get_close_matches(
                    str((scan_computer_name, box_id)),
                    (str(batch_key) for batch_key in batches_by_key),
                    n=1,
                )
                closest_match = (
                    ast.literal_eval(close_matches[0]) if close_matches else None
                )
                raise UserError(
                    "Invalid ScanComputerName/BoxID for row with"
                    f" RowNumber {row_number}: {scan_computer_name}, {box_id}."
                    " The ScanComputerName and BoxID fields in the CVR file"
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

        cvr_file.close()

    return contests_metadata, parse_cvr_rows()


def parse_dominion_cvrs(
    jurisdiction: Jurisdiction,
) -> Tuple[CVR_CONTESTS_METADATA, Iterable[CvrBallot]]:
    cvr_file = retrieve_file(jurisdiction.cvr_file.storage_path)
    cvrs = csv_reader_for_cvr(cvr_file)

    # Parse out all the initial metadata
    _election_name = next(cvrs)[0]
    contest_row = [" ".join(contest.splitlines()) for contest in next(cvrs)]
    first_contest_column = next(c for c, value in enumerate(contest_row) if value != "")
    contest_headers = contest_row[first_contest_column:]
    contest_choices = next(cvrs)[first_contest_column:]
    headers_and_affiliations = next(cvrs)

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
    contests_metadata: CVR_CONTESTS_METADATA = defaultdict(
        lambda: dict(choices=dict(), votes_allowed=0, total_ballots_cast=0)
    )
    for column, (contest_name, votes_allowed, choice_name) in enumerate(
        zip(contest_names, contest_votes_allowed, contest_choices)
    ):
        contests_metadata[contest_name]["votes_allowed"] = votes_allowed
        contests_metadata[contest_name]["choices"][choice_name] = dict(
            # Store the column index of this contest choice so we can parse
            # interpretations later
            column=column,
            num_votes=0,  # Will be counted while parsing rows
        )
        # Will be counted while parsing rows
        contests_metadata[contest_name]["total_ballots_cast"] = 0

    batches_by_key = {
        (batch.tabulator, batch.name): batch for batch in jurisdiction.batches
    }
    header_indices = get_header_indices(headers_and_affiliations[:first_contest_column])

    def parse_cvr_rows() -> Iterable[CvrBallot]:
        for row_index, row in enumerate(cvrs):
            cvr_number = column_value(row, "CvrNumber", row_index + 1, header_indices)
            tabulator_number = column_value(
                row, "TabulatorNum", cvr_number, header_indices
            )
            batch_id = column_value(row, "BatchId", cvr_number, header_indices)
            record_id = column_value(row, "RecordId", cvr_number, header_indices)

            # When parsing ImprintedId, fall back to UniqueVotingIdentifer
            # (but only if that column is present in the CVR at all)
            imprinted_id = column_value(
                row,
                "ImprintedId",
                cvr_number,
                header_indices,
                required="UniqueVotingIdentifier" not in header_indices,
            ) or column_value(
                row, "UniqueVotingIdentifier", cvr_number, header_indices,
            )

            interpretations = row[first_contest_column:]

            db_batch = batches_by_key.get((tabulator_number, batch_id))

            if db_batch:
                yield CvrBallot(
                    batch=db_batch,
                    record_id=int(record_id),
                    imprinted_id=imprinted_id,
                    interpretations=",".join(interpretations),
                )
            else:
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

        cvr_file.close()

    return contests_metadata, parse_cvr_rows()


def parse_ess_cvrs(
    jurisdiction: Jurisdiction,
) -> Tuple[CVR_CONTESTS_METADATA, Iterable[CvrBallot]]:
    # Parsing ES&S CVRs is more complicated than, say, Dominion.
    # There are two main data sources:
    #  - a list of ballots with their batch/tabulator metadata
    #  - a list of CVR data (the actual interpretations)
    # We have to join them together using a unique id for each ballot (the CVR
    # number). What's more, the list of ballots might be split across multiple files.
    #
    # Here's a rough outline of the process:
    # 1. Unzip and decode the files
    # 2. Detect and sort out which files are ballot metadata and which is the CVR data
    # 3. For each ballot file, parse the metadata into CVRBallot objects (w/o interpretations)
    # 4. For the CVR file, make two passes:
    #   - First, parse out the contest and choice names. We have to do this in
    #     a separate pass since our storage scheme for interpretations requires
    #     knowing all of the contest and choice names up front, and the ES&S
    #     format doesn't tell you that - you have to look at every row.
    #   - Second, parse out the interpretations.
    # 5. Concatenate the parsed CVRBallot lists and join that to the parsed interpretation

    zip_file = retrieve_file(jurisdiction.cvr_file.storage_path)
    files = unzip_files(zip_file)
    zip_file.close()

    def decode_file(file: IO[bytes], name: str) -> TextIO:
        try:
            validate_not_empty(file)
            return decode_csv(file)
        except UserError as error:
            raise UserError(f"{name}: {error}") from error

    text_files = {name: decode_file(file, name) for name, file in files.items()}

    def is_ballots_file(file: TextIO):
        first_line = file.readline()
        file.seek(0)
        return first_line.startswith("Ballots")

    ballots_files = {
        name: file for name, file in text_files.items() if is_ballots_file(file)
    }
    cvr_files = {
        name: file for name, file in text_files.items() if not is_ballots_file(file)
    }

    if len(ballots_files) == 0:
        raise UserError(
            "Missing ballots files - at least one file should contain the list of tabulated ballots and their corresponding CVR identifiers."
        )
    if len(cvr_files) == 0:
        raise UserError(
            "Missing CVR file - one exported file should contain the cast vote records for each ballot."
        )
    if len(cvr_files) > 1:
        raise UserError(
            "Could not detect which files contain the list of ballots and which contains the CVR results. Please ensure you have one file with the cast vote records for each ballot and at least one file containing the list of tabulated ballots and their corresponding CVR identifiers."
        )

    [(cvr_file_name, cvr_file)] = cvr_files.items()

    batches_by_key = {
        (batch.tabulator, batch.name): batch for batch in jurisdiction.batches
    }

    def parse_ballots_csv(
        ballots_csv: CSVIterator,
    ) -> Iterable[Tuple[str, CvrBallot]]:  # (CVR number, ballot)
        # Skip some metadata rows
        # pylint: disable=stop-iteration-return
        _ballots_header = next(ballots_csv)
        _gen_tag = next(ballots_csv)
        _county_name = next(ballots_csv)
        _date = next(ballots_csv)
        _empty_row = next(ballots_csv)

        headers = next(ballots_csv)
        header_indices = get_header_indices(headers)

        tabulator_regex = re.compile(r"^(\d{4})(\d{6})$")

        for row_index, row in enumerate(ballots_csv):
            if row[0].startswith("Total"):
                continue
            cvr_number = column_value(
                row, "Cast Vote Record", row_index + 1, header_indices
            )
            batch_name = column_value(row, "Batch", cvr_number, header_indices)
            tabulator_cvr = column_value(
                row, "Tabulator CVR", cvr_number, header_indices
            )

            match = tabulator_regex.match(tabulator_cvr)
            if not match:
                raise UserError(
                    "Tabulator CVR should be a ten-digit number."
                    f" Got {tabulator_cvr} for Cast Vote Record {cvr_number}."
                    " Make sure any leading zeros have not been stripped from this field."
                )
            tabulator_number, ballot_number = match.groups()

            db_batch = batches_by_key.get((tabulator_number, batch_name))
            if db_batch:
                yield (
                    cvr_number,
                    CvrBallot(
                        batch=db_batch,
                        record_id=int(ballot_number),
                        imprinted_id=tabulator_cvr,
                    ),
                )
            else:
                close_matches = difflib.get_close_matches(
                    str((tabulator_number, batch_name)),
                    (str(batch_key) for batch_key in batches_by_key),
                    n=1,
                )
                closest_match = (
                    ast.literal_eval(close_matches[0]) if close_matches else None
                )
                raise UserError(
                    "Invalid Tabulator/Batch for row with"
                    f" Cast Vote Record {cvr_number}: {tabulator_number}, {batch_name}."
                    " The Tabulator and Batch fields in the CVR file"
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

    def parse_contest_metadata(cvr_csv: CSVIterator) -> CVR_CONTESTS_METADATA:
        headers = next(cvr_csv)
        # Based on files we've seen, the first 3 columns are Cast Vote Record,
        # Precinct, Ballot Style and the rest are contest names
        first_contest_column = 3
        contest_names = headers[first_contest_column:]
        # Since "overvote" and "undervote" are treated like choices in ES&S
        # CVRs, we want to make sure they are always part of the parsed choice
        # list so that they always appear to audit boards.
        contest_choices: Dict[str, Set[str]] = {
            contest_name: {"overvote", "undervote"} for contest_name in contest_names
        }

        header_indices = get_header_indices(headers)

        for row_index, row in enumerate(cvr_csv):
            for contest_name in contest_names:
                choice_name = column_value(
                    row, contest_name, row_index + 1, header_indices, required=False
                )
                if choice_name:
                    contest_choices[contest_name].add(choice_name)

        # Assign each choice a column index in the interpretation string
        contest_choice_pairs = [
            (contest_name, contest_choice)
            for contest_name, choices in contest_choices.items()
            for contest_choice in sorted(choices)
        ]
        contest_choice_columns = {
            choice: column for column, choice in enumerate(contest_choice_pairs)
        }

        return {
            contest_name: dict(
                # Until we know how vote-for-n contests are serialized in the
                # ES&S CVR, we assume vote-for-1
                votes_allowed=1,
                choices={
                    choice: dict(
                        column=contest_choice_columns[(contest_name, choice)],
                        num_votes=0,  # Will be counted while parsing rows
                    )
                    for choice in sorted(choices)
                },
                total_ballots_cast=0,  # Will be counted while parsing rows
            )
            for contest_name, choices in contest_choices.items()
            if len(choices) > 0
        }

    def parse_interpretations(
        cvr_csv: CSVIterator, contests_metadata: CVR_CONTESTS_METADATA
    ) -> Iterable[Tuple[str, str]]:  # (CVR number, interpretations)
        # pylint: disable=stop-iteration-return
        headers = next(cvr_csv)
        header_indices = get_header_indices(headers)

        max_interpretation_column = max(
            choice_metadata["column"]
            for contest_metadata in contests_metadata.values()
            for choice_metadata in contest_metadata["choices"].values()
        )

        def parse_row_interpretations(row: List[str], cvr_number: int,) -> str:
            interpretations = ["" for _ in range(max_interpretation_column + 1)]
            for contest_name, contest_metadata in contests_metadata.items():
                recorded_choice = column_value(
                    row, contest_name, cvr_number, header_indices, required=False
                )
                if recorded_choice:
                    for choice_name, choice_metadata in contest_metadata[
                        "choices"
                    ].items():
                        if choice_name == recorded_choice:
                            interpretations[choice_metadata["column"]] = "1"
                        else:
                            interpretations[choice_metadata["column"]] = "0"

            return ",".join(interpretations)

        try:
            for row_index, row in enumerate(cvr_csv):
                cvr_number = column_value(
                    row, "Cast Vote Record", row_index + 1, header_indices
                )
                yield (cvr_number, parse_row_interpretations(row, cvr_number))
        except UserError as error:
            raise UserError(f"{cvr_file_name}: {error}") from error
        finally:
            cvr_file.close()

    def parse_and_concat_ballots_files(
        ballots_files: Dict[str, TextIO]
    ) -> Iterable[Tuple[str, CvrBallot]]:
        for name, ballots_file in ballots_files.items():
            try:
                validate_comma_delimited(ballots_file)
                ballots_csv = csv.reader(ballots_file, delimiter=",")
                yield from parse_ballots_csv(ballots_csv)
            except UserError as error:
                raise UserError(f"{name}: {error}") from error
            finally:
                ballots_file.close()

    def join_ballots_to_interpretations(
        all_ballots: Iterable[Tuple[str, CvrBallot]],
        all_interpretations: Iterable[Tuple[str, str]],
    ) -> Iterable[CvrBallot]:
        for cvr_ballot, cvr_interpretations in itertools.zip_longest(
            all_ballots, all_interpretations
        ):
            mismatch_error = UserError(
                "Mismatch between CVR file and ballots files."
                " Make sure the Cast Vote Record column in the CVR file and"
                " the ballots file match and include exactly the same set of ballots."
            )
            if cvr_interpretations is None or cvr_ballot is None:
                raise mismatch_error
            (ballot_cvr_number, ballot) = cvr_ballot
            (interpretations_cvr_number, interpretations) = cvr_interpretations
            if ballot_cvr_number != interpretations_cvr_number:
                raise mismatch_error
            ballot.interpretations = interpretations
            yield ballot

    ballots = parse_and_concat_ballots_files(ballots_files)
    try:
        validate_comma_delimited(cvr_file)
        cvr_csv = csv.reader(cvr_file, delimiter=",")
        contests_metadata = parse_contest_metadata(cvr_csv)
        cvr_file.seek(0)
        interpretations = parse_interpretations(cvr_csv, contests_metadata)
        return (
            contests_metadata,
            join_ballots_to_interpretations(ballots, interpretations),
        )
    except UserError as error:
        raise UserError(f"{cvr_file_name}: {error}") from error


@background_task
def process_cvr_file(
    jurisdiction_id: str,
    jurisdiction_admin_email: str,
    support_user_email: Optional[str],
    emit_progress,
):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    def process() -> None:
        # Ideally, the CVR should have the same number of ballots as the
        # manifest, so we can use that as an approximation of the file parsing
        # progress since we're streaming the file and don't know the size up front.
        total_records = jurisdiction.manifest_num_ballots
        emit_progress(0, total_records)

        # Parse ballot rows and contest metadata
        def parse_cvrs():
            if jurisdiction.cvr_file_type == CvrFileType.DOMINION:
                return parse_dominion_cvrs(jurisdiction)
            elif jurisdiction.cvr_file_type == CvrFileType.CLEARBALLOT:
                return parse_clearballot_cvrs(jurisdiction)
            elif jurisdiction.cvr_file_type == CvrFileType.ESS:
                return parse_ess_cvrs(jurisdiction)
            else:
                raise Exception(
                    f"Unsupported CVR file type: {jurisdiction.cvr_file_type}"
                )  # pragma: no cover

        contests_metadata, cvr_ballots = parse_cvrs()

        # Store ballot rows as CvrBallots in the database. Since we may have
        # millions of rows, we write this data into a tempfile and load it into
        # the db using the COPY command (muuuuch faster than INSERT).
        with tempfile.TemporaryFile(mode="w+") as ballots_tempfile:
            ballots_csv = csv.writer(ballots_tempfile)
            for i, cvr_ballot in enumerate(cvr_ballots):
                if i % 1000 == 0:
                    emit_progress(i, total_records)
                # For hybrid audits, skip any batches that were marked as not
                # having CVRs in the manifest
                if (
                    jurisdiction.election.audit_type == AuditType.HYBRID
                    and not cvr_ballot.batch.has_cvrs
                ):
                    continue

                ballots_csv.writerow(
                    [
                        cvr_ballot.batch.id,
                        cvr_ballot.record_id,
                        cvr_ballot.imprinted_id,
                        cvr_ballot.interpretations,
                    ]
                )

                # Add to our running totals for ContestChoice.num_votes and
                # Contest.total_ballots_cast
                interpretations = cvr_ballot.interpretations.split(",")
                contests_on_ballot = set()
                for contest_name, contest_metadata in contests_metadata.items():
                    contest_interpretations = {
                        choice_name: interpretations[choice_metadata["column"]]
                        for choice_name, choice_metadata in contest_metadata[
                            "choices"
                        ].items()
                    }
                    # Skip contests not on ballot
                    if any(
                        interpretation == ""
                        for interpretation in contest_interpretations.values()
                    ):
                        continue
                    contests_on_ballot.add(contest_name)

                    # Skip overvotes
                    votes = sum(
                        int(interpretation)
                        for interpretation in contest_interpretations.values()
                    )
                    if votes > contest_metadata["votes_allowed"]:
                        continue

                    for choice_name, interpretation in contest_interpretations.items():
                        contest_metadata["choices"][choice_name]["num_votes"] += int(
                            interpretation
                        )

                for contest_name in contests_on_ballot:
                    contests_metadata[contest_name]["total_ballots_cast"] += 1

            jurisdiction.cvr_contests_metadata = contests_metadata

            # In order to use the COPY command, we have to get the raw psycopg2
            # connection. Note that we use the underlying connection from the
            # db_session, so the operation will occur within the same
            # transaction.
            cursor = db_session.connection().connection.cursor()
            ballots_tempfile.seek(0)
            try:
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
            except Exception as exc:
                raise exc
            finally:
                cursor.close()

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

        contests.set_contest_metadata(jurisdiction.election)

        emit_progress(total_records, total_records)

    error = None
    try:
        process()
    except Exception as exc:
        error = str(exc) or str(exc.__class__.__name__)
        if isinstance(exc, UserError):
            raise exc
        # Catch all unexpected errors and wrap them with a generic message.
        raise Exception("Could not parse CVR file") from exc
    finally:
        session = Session(db_engine)
        jurisdiction = session.query(Jurisdiction).get(jurisdiction_id)
        base = activity_base(jurisdiction.election)
        base.user_type = UserType.JURISDICTION_ADMIN
        base.user_key = jurisdiction_admin_email
        base.support_user_email = support_user_email
        record_activity(
            UploadFile(
                timestamp=jurisdiction.cvr_file.uploaded_at,
                base=base,
                jurisdiction_id=jurisdiction.id,
                jurisdiction_name=jurisdiction.name,
                file_type="cvrs",
                error=error,
            ),
            session,
        )
        session.commit()


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

    validate_csv_mimetype(request.files["cvrs"])

    if request.form.get("cvrFileType") not in [
        cvr_file_type.value for cvr_file_type in CvrFileType
    ]:
        raise BadRequest("Invalid file type")


def clear_cvr_data(jurisdiction: Jurisdiction):
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
    clear_cvr_data(jurisdiction)

    if request.form["cvrFileType"] == CvrFileType.ESS:
        file_name = "cvr-files.zip"
        zip_file = zip_files(
            {file.filename: file.stream for file in request.files.getlist("cvrs")}
        )
        storage_path = store_file(
            zip_file,
            f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
            + timestamp_filename("cvrs", "zip"),
        )
    else:
        file_name = request.files["cvrs"].filename
        storage_path = store_file(
            request.files["cvrs"].stream,
            f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
            + timestamp_filename("cvrs", "csv"),
        )

    jurisdiction.cvr_file = File(
        id=str(uuid.uuid4()),
        name=file_name,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    jurisdiction.cvr_file_type = request.form["cvrFileType"]
    jurisdiction.cvr_file.task = create_background_task(
        process_cvr_file,
        dict(
            jurisdiction_id=jurisdiction.id,
            jurisdiction_admin_email=get_loggedin_user(session)[1],
            support_user_email=get_support_user(session),
        ),
    )
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs", methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_cvrs(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    file = serialize_file(jurisdiction.cvr_file)
    return jsonify(
        file=file and dict(file, cvrFileType=jurisdiction.cvr_file_type),
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

    return csv_response(
        retrieve_file(jurisdiction.cvr_file.storage_path), jurisdiction.cvr_file.name
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/cvrs", methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def clear_cvrs(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if jurisdiction.cvr_file_id:
        File.query.filter_by(id=jurisdiction.cvr_file_id).delete()
        clear_cvr_data(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
