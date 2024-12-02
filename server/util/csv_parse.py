# pylint: disable=stop-iteration-return
from collections import defaultdict
from enum import Enum
from typing import (
    IO,
    BinaryIO,
    Iterable,
    List,
    Iterator,
    Dict,
    Any,
    NamedTuple,
    TextIO,
    Tuple,
    TypeVar,
    Union,
)
import csv as py_csv
import io, re, locale, chardet

from .jsonschema import EMAIL_REGEX
from .collections import find_first_duplicate
from ..worker.tasks import UserError

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


class CSVParseError(UserError):
    pass


class CSVValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    YES_NO = "yes_no"


class CSVColumnType(NamedTuple):
    name: str
    value_type: CSVValueType
    # Must the the column header be present?
    required_column: bool = True
    # Can a row in the column be empty?
    allow_empty_rows: bool = False
    unique: bool = False


CSVRow = List[str]
CSVIterator = Iterator[CSVRow]
CSVDictIterator = Iterator[Dict[str, Any]]

INVALID_CSV_ERROR = (
    "Please submit a valid CSV."
    " If you are working with an Excel spreadsheet,"
    " make sure you export it as a .csv file before uploading."
)


# Robust CSV parsing
# "Be conservative in what you do, be liberal in what you accept from others"
# https://en.wikipedia.org/wiki/Robustness_principle
def parse_csv(file: BinaryIO, columns: List[CSVColumnType]) -> CSVDictIterator:
    validate_not_empty(file)
    text_file = decode_csv(file)
    validate_comma_delimited(text_file)
    csv: CSVIterator = py_csv.reader(text_file, delimiter=",")
    csv = strip_whitespace(csv)
    csv = reject_no_rows(csv)
    csv = skip_empty_trailing_columns(csv)
    csv = validate_and_normalize_headers(csv, columns)
    dict_csv = convert_rows_to_dicts(csv)
    dict_csv = reject_empty_cells(dict_csv, columns)
    dict_csv = reject_total_rows(dict_csv)
    dict_csv = validate_and_parse_values(dict_csv, columns)
    dict_csv = reject_duplicate_values(dict_csv, columns)
    # Filter out empty rows towards the end so we can get accurate row numbers
    # in all the other checkers
    dict_csv = skip_empty_rows(dict_csv)
    dict_csv = reject_final_total_row(dict_csv, columns)

    return dict_csv


def is_filetype_csv_mimetype(file_type: str) -> bool:
    return file_type in ["text/csv", "application/vnd.ms-excel"]


def read_chunks(file: IO[bytes], chunk_size: int) -> Iterable[bytes]:
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        yield chunk


def decode_csv(file: IO[bytes]) -> TextIO:
    detector = chardet.UniversalDetector()
    for i, chunk in enumerate(read_chunks(file, 64)):
        detector.feed(chunk)
        if detector.done or i > 500:
            break
    detector.close()
    encoding = detector.result["encoding"]
    if not encoding:
        raise CSVParseError(INVALID_CSV_ERROR)
    if encoding == "ascii":
        encoding = "utf-8"

    # chardet sometimes detects an encoding with a low confidence threshold. To be extra safe, try
    # reading the first line of the file with the detected encoding before returning the file. This
    # check catches unusual cases like XLS files mislabeled with a .csv extension
    file.seek(0)
    try:
        line = file.readline()
        line.decode(encoding)
    except UnicodeDecodeError as error:
        raise CSVParseError(
            INVALID_CSV_ERROR
            + f"\n\nAdditional details: Unable to decode file assuming {encoding} encoding"
        ) from error

    # Just to be safe, if we still got the encoding wrong and there are
    # undecodable characters deeper in the file, turn on the "replace errors"
    # option to replace any invalid chars with a question mark so we don't crash.
    file.seek(0)
    return io.TextIOWrapper(file, encoding=encoding, errors="replace", newline=None)


def validate_not_empty(file: IO[bytes]):
    if file.read(1) == b"":
        raise CSVParseError("CSV cannot be empty.")
    file.seek(0)


def validate_comma_delimited(file: TextIO):
    line = file.readline()
    file.seek(0)

    dialect = None
    try:
        dialect = py_csv.Sniffer().sniff(line)
        if dialect.delimiter in (",", "i"):
            return
    except Exception:
        pass

    detail = ""
    if dialect and dialect.delimiter == "\t":
        detail = " This file has columns separated by tabs."
    raise CSVParseError(
        "Please submit a valid CSV file with columns separated by commas." + detail
    )


def strip_whitespace(csv: CSVIterator) -> CSVIterator:
    return ([cell.strip() for cell in row] for row in csv)


def reject_no_rows(csv: CSVIterator) -> CSVIterator:
    yield next(csv)
    second = next(csv, None)
    if second is None:
        raise CSVParseError("CSV must contain at least one row after headers.")
    yield second
    yield from csv


def skip_empty_trailing_columns(csv: CSVIterator) -> CSVIterator:
    headers = next(csv)

    # Count empty trailing columns so we can ignore them.
    empty_trailing_header_count = 0
    for header in reversed(headers):
        if len(header) == 0:
            empty_trailing_header_count += 1
        else:
            break

    if empty_trailing_header_count == 0:
        # No empty trailing columns, just send the data through as-is.
        yield headers
        yield from csv
    else:
        yield headers[0:-empty_trailing_header_count]
        for r, row in enumerate(csv):  # pylint: disable=invalid-name
            for empty_trailing_column_index, cell in enumerate(
                row[-empty_trailing_header_count:]
            ):
                if len(cell) > 0:
                    raise CSVParseError(
                        f"Empty trailing column {len(headers) - empty_trailing_header_count + empty_trailing_column_index + 1}"
                        f" expected to have no values, but row {r+2} has a value: {cell}."
                    )

            # Pass only cells for non-empty columns.
            yield row[0:-empty_trailing_header_count]


def validate_and_normalize_headers(
    csv: CSVIterator, columns: List[CSVColumnType]
) -> CSVIterator:
    headers = next(csv)

    normalized_headers = [
        next((c.name for c in columns if c.name.lower() == header.lower()), header)
        for header in headers
    ]

    if find_first_duplicate(normalized_headers):
        raise CSVParseError("Column headers must be unique.")

    allowed_headers = {c.name for c in columns}
    required_headers = {c.name for c in columns if c.required_column}

    missing_headers = required_headers - set(normalized_headers)
    if len(missing_headers) > 0:
        raise CSVParseError(
            f"Missing required {pluralize('column', len(missing_headers))}:"
            f" {', '.join(sorted(missing_headers))}."
        )

    unexpected_headers = set(normalized_headers) - allowed_headers
    if len(unexpected_headers) > 0:
        raise CSVParseError(
            f"Found unexpected columns. Allowed columns: {', '.join(sorted(allowed_headers))}."
        )

    yield normalized_headers
    yield from csv


def is_empty_row(row: Dict[str, Any]) -> bool:
    return all(value == "" for value in row.values())


def skip_empty_rows(csv: CSVDictIterator) -> CSVDictIterator:
    for row in csv:
        if not is_empty_row(row):
            yield row


def reject_empty_cells(
    csv: CSVDictIterator, columns: List[CSVColumnType]
) -> CSVDictIterator:
    columns_by_header = {column.name: column for column in columns}

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        # Skip empty rows, we filter them out later
        if is_empty_row(row):
            yield row
            continue

        for header, value in row.items():  # pylint: disable=invalid-name
            if value == "" and not columns_by_header[header].allow_empty_rows:
                raise CSVParseError(
                    f"A value is required for the cell at column {header}, row {r+2}."
                )
        yield row


def validate_and_parse_values(
    csv: CSVDictIterator, columns: List[CSVColumnType]
) -> CSVDictIterator:
    columns_by_header = {column.name: column for column in columns}

    def parse_and_validate_value(header, value, r):  # pylint: disable=invalid-name
        where = f"column {header}, row {r+2}"
        column = columns_by_header[header]

        if column.allow_empty_rows and value == "":
            return None

        if column.value_type is CSVValueType.NUMBER:
            try:
                return locale.atoi(value)
            except ValueError:
                # pylint: disable=raise-missing-from
                raise CSVParseError(f"Expected a number in {where}. Got: {value}.")

        if column.value_type is CSVValueType.EMAIL:
            if not EMAIL_REGEX.match(value):
                raise CSVParseError(
                    f"Expected an email address in {where}. Got: {value}."
                )

        if column.value_type is CSVValueType.YES_NO:
            if value.lower() in ["y", "yes"]:
                return True
            if value.lower() in ["n", "no"]:
                return False
            raise CSVParseError(f"Expected Y or N in {where}. Got: {value}.")

        return value

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        # Skip empty rows, we filter them out later
        if is_empty_row(row):
            yield row
            continue

        yield {
            header: parse_and_validate_value(header, value, r)
            for header, value in row.items()
        }


def format_tuple(tup: Tuple) -> str:
    return str(tup[0]) if len(tup) == 1 else str(tup)


def reject_duplicate_values(
    csv: CSVDictIterator, columns: List[CSVColumnType]
) -> CSVDictIterator:
    # For our purposes, we want all the columns with unique=True to be used as
    # one composite unique key for the rows.
    unique_columns = tuple(sorted(column.name for column in columns if column.unique))
    if len(unique_columns) == 0:
        yield from csv
        return

    seen = set()
    for row in csv:
        # Skip empty rows, we filter them out later
        if is_empty_row(row):
            yield row
            continue

        row_key = tuple(row[column] for column in unique_columns)
        if row_key in seen:
            raise CSVParseError(
                f"Each row must be uniquely identified by {format_tuple(unique_columns)}."
                + f" Found duplicate: {format_tuple(row_key)}."
            )
        else:
            seen.add(row_key)

        yield row


TOTAL_REGEX = re.compile(r"(^|[^a-zA-Z])(sub)?totals?($|[^a-zA-Z])", re.IGNORECASE)


def reject_total_rows(csv: CSVDictIterator) -> CSVDictIterator:
    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        for value in row.values():
            if TOTAL_REGEX.search(value):
                raise CSVParseError(
                    f"It looks like you might have a total row (row {r+2})."
                    " Please remove this row from the CSV."
                )
        yield row


def reject_final_total_row(csv: CSVDictIterator, columns: List[CSVColumnType]):
    numeric_column_values = defaultdict(list)

    for row in csv:
        for column in columns:
            value = row.get(column.name)
            if column.value_type == CSVValueType.NUMBER and value is not None:
                numeric_column_values[column.name].append(value)
        yield row

    if len(numeric_column_values) > 0 and all(
        sum(values[:-1]) == values[-1] and values[-1] != 0
        for values in numeric_column_values.values()
    ):
        raise CSVParseError(
            "It looks like the last row in the CSV might be a total row."
            " Please remove this row from the CSV."
        )


def convert_rows_to_dicts(csv: CSVIterator) -> CSVDictIterator:
    headers = next(csv)

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        # Normalize empty rows to make sure we can turn them into dicts.
        # We'll filter them out later.
        if len(row) == 0:
            row = ["" for _ in headers]
        if len(row) != len(headers):
            raise CSVParseError(
                f"Wrong number of cells in row {r+2}."
                f" Expected {len(headers)} {pluralize('cell', len(headers))},"
                f" got {len(row)} {pluralize('cell', len(row))}."
            )

        yield dict(zip(headers, row))


def pluralize(word: str, num: int) -> str:
    return word if num == 1 else f"{word}s"


def get_header_indices(headers_row: List[str]) -> Dict[str, int]:
    return {header: i for i, header in enumerate(headers_row)}


# Allow a 2-string tuple for Dominion's two-row CSV headers
# pylint: disable=invalid-name
HeaderType = TypeVar("HeaderType", str, Tuple[str, str])


def column_value(
    row: List[str],
    header: HeaderType,
    row_number: int,
    header_indices: Dict[HeaderType, int],
    required: bool = True,
    file_name: str = None,
    remove_leading_equal_sign: bool = False,
    header_readable_string_override: Union[str, None] = None,
):
    header_readable_string: str = header_readable_string_override or str(header)
    index = header_indices.get(header)
    if index is None:
        if required:
            raise UserError(
                f"Missing required column {header_readable_string} in {file_name}."
                if file_name is not None
                else f"Missing required column {header_readable_string}."
            )
        # We haven't seen CVRs with entirely optional columns, so it's hard to test this case
        return None  # pragma: no cover
    value = row[index] if index < len(row) else None
    if required and (value is None or value == ""):
        raise UserError(
            f"Missing required column {header_readable_string} in row {row_number} in {file_name}."
            if file_name is not None
            else f"Missing required column {header_readable_string} in row {row_number}."
        )
    # Dominion sometimes exports CVR CSVs with equal signs in front of certain columns' values,
    # e.g. ="3",="1002",="1",="10",="1002-1-10","Mail-in",...
    if (
        remove_leading_equal_sign
        and value
        and value.startswith('="')
        and value.endswith('"')
    ):
        value = value[2:-1]
    return value
