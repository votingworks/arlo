# pylint: disable=stop-iteration-return
from enum import Enum
from typing import List, Iterator, Dict, Any, NamedTuple, Set
import csv as py_csv
import io, re, locale, chardet
from werkzeug.exceptions import BadRequest
from .process_file import UserError

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


class CSVParseError(UserError):
    pass


class CSVValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"


class CSVColumnType(NamedTuple):
    name: str
    value_type: CSVValueType
    required: bool = True
    unique: bool = False


# https://emailregex.com/
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

CSVRow = List[str]
CSVIterator = Iterator[CSVRow]
CSVDictIterator = Iterator[Dict[str, Any]]

# Robust CSV parsing
# "Be conservative in what you do, be liberal in what you accept from others"
# https://en.wikipedia.org/wiki/Robustness_principle
def parse_csv(csv_string: str, columns: List[CSVColumnType]) -> CSVDictIterator:
    validate_is_csv(csv_string)
    csv: CSVIterator = py_csv.reader(io.StringIO(csv_string), delimiter=",")
    csv = strip_whitespace(csv)
    csv = reject_no_rows(csv)
    csv = skip_empty_trailing_columns(csv)
    csv = validate_headers(csv, columns)
    csv = reject_empty_cells(csv, columns)
    csv = reject_total_rows(csv)
    csv = validate_and_parse_values(csv, columns)
    csv = reject_duplicate_values(csv, columns)
    # Filter out empty rows last so we can get accurate row numbers in all the
    # other checkers
    csv = skip_empty_rows(csv)
    return convert_rows_to_dicts(csv, columns)


def validate_is_csv(csv: str):
    lines = csv.splitlines()
    if len(lines) == 0:
        raise CSVParseError("CSV cannot be empty.")

    dialect = None
    try:
        dialect = py_csv.Sniffer().sniff(lines[0])
        if dialect.delimiter == "," or dialect.delimiter == "i":
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
            for (empty_trailing_column_index, cell) in enumerate(
                row[-empty_trailing_header_count:]
            ):
                if len(cell) > 0:
                    raise CSVParseError(
                        f"Empty trailing column {len(headers) - empty_trailing_header_count + empty_trailing_column_index + 1}"
                        f" expected to have no values, but row {r+2} has a value: {cell}."
                    )

            # Pass only cells for non-empty columns.
            yield row[0:-empty_trailing_header_count]


def validate_headers(csv: CSVIterator, columns: List[CSVColumnType]) -> CSVIterator:
    headers = next(csv)
    lowercase_headers = [header.lower() for header in headers]

    allowed_headers = [c.name for c in columns]
    required_headers = [c.name for c in columns if c.required]

    missing_headers = [
        required_header
        for required_header in required_headers
        if required_header.lower() not in lowercase_headers
    ]
    if len(missing_headers) > 0:
        raise CSVParseError(
            f"Missing required {pluralize('column', len(missing_headers))}:"
            f" {', '.join(missing_headers)}."
        )

    lowercase_allowed_headers = [h.lower() for h in allowed_headers]
    unexpected_headers = [
        header for header in headers if header.lower() not in lowercase_allowed_headers
    ]
    if len(unexpected_headers) > 0:
        raise CSVParseError(
            f"Found unexpected columns. Allowed columns: {', '.join(allowed_headers)}."
        )

    ordered_headers = [h for h in allowed_headers if h.lower() in lowercase_headers]
    lowercase_ordered_headers = [h.lower() for h in ordered_headers]
    if lowercase_ordered_headers != lowercase_headers:
        raise CSVParseError(
            f"Columns out of order. Expected order: {', '.join(ordered_headers)}."
        )

    yield headers
    yield from csv


def is_empty_row(row: List[str]):
    return len(row) == 0 or all(value == "" for value in row)


def skip_empty_rows(csv: CSVIterator) -> CSVIterator:
    for row in csv:
        if not is_empty_row(row):
            yield row


def reject_empty_cells(csv: CSVIterator, columns: List[CSVColumnType]) -> CSVIterator:
    headers = next(csv)
    yield headers

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        # Don't check empty rows, we filter them out elsewhere
        if is_empty_row(row):
            continue
        if len(row) != len(headers):
            raise CSVParseError(
                f"Wrong number of cells in row {r+2}."
                f" Expected {len(headers)} {pluralize('cell', len(headers))},"
                f" got {len(row)} {pluralize('cell', len(row))}."
            )
        for c, value in enumerate(row):  # pylint: disable=invalid-name
            if columns[c].required and value == "":
                raise CSVParseError(
                    "All cells must have values."
                    f" Got empty cell at column {headers[c]}, row {r+2}."
                )
        yield row


def validate_and_parse_values(
    csv: CSVIterator, columns: List[CSVColumnType]
) -> CSVIterator:
    yield next(csv)  # Skip the headers

    def parse_and_validate_value(column, value, r):  # pylint: disable=invalid-name
        where = f"column {column.name}, row {r+2}"

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

        return value

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        yield [
            parse_and_validate_value(column, value, r)
            for column, value in zip(columns, row)
        ]


def reject_duplicate_values(
    csv: CSVIterator, columns: List[CSVColumnType]
) -> CSVIterator:
    yield next(csv)  # Skip the headers

    seen: Dict[str, Set[str]] = {column.name: set() for column in columns}
    for row in csv:
        for column, value in zip(columns, row):
            if column.unique and value in seen[column.name]:
                raise CSVParseError(
                    f"Values in column {column.name} must be unique."
                    + f" Found duplicate value: {value}."
                )
            else:
                seen[column.name].add(value)

        yield row


def reject_total_rows(csv: CSVIterator) -> CSVIterator:
    yield next(csv)  # Skip the headers

    for r, row in enumerate(csv):  # pylint: disable=invalid-name
        for value in row:
            if value.lower() in ["total", "totals"]:
                raise CSVParseError(f"Remove total row (row {r+2})")

        yield row


def convert_rows_to_dicts(
    csv: CSVIterator, columns: List[CSVColumnType]
) -> CSVDictIterator:
    next(csv)  # Skip headers
    headers = [c.name for c in columns]
    return (dict(zip(headers, row)) for row in csv)


def pluralize(word: str, num: int) -> str:
    return word if num == 1 else f"{word}s"


def decode_csv_file(file: bytes) -> str:
    try:
        try:
            return file.decode("utf-8-sig")
        except UnicodeDecodeError:
            detect_result = chardet.detect(file)
            if not detect_result["encoding"]:
                raise
            return file.decode(detect_result["encoding"])
    except UnicodeDecodeError:
        # pylint: disable=raise-missing-from
        raise BadRequest(
            "Please submit a valid CSV."
            " If you are working with an Excel spreadsheet,"
            " make sure you export it as a .csv file before uploading"
        )
