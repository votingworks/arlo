import io, itertools, re, locale, chardet
from enum import Enum
from typing import List, Tuple, Iterator, Dict, Any
import csv as py_csv
from werkzeug.exceptions import BadRequest
from util.process_file import UserError


class CSVParseError(UserError):
    pass


class CSVValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"


# https://emailregex.com/
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


CSVColumnTypes = List[Tuple[str, CSVValueType, bool]]

CSVRow = List[str]
CSVIterator = Iterator[CSVRow]
CSVDictIterator = Iterator[Dict[str, Any]]

# Robust CSV parsing
# "Be conservative in what you do, be liberal in what you accept from others"
# https://en.wikipedia.org/wiki/Robustness_principle
def parse_csv(csv_string: str, columns: CSVColumnTypes) -> CSVDictIterator:
    validate_is_csv(csv_string)
    csv: CSVIterator = py_csv.reader(io.StringIO(csv_string), delimiter=",")
    csv = strip_whitespace(csv)
    csv = reject_empty(csv)
    csv = validate_headers(csv, columns)
    csv = skip_empty_rows(csv)
    csv = reject_empty_cells(csv, columns)
    csv = validate_values(csv, columns)
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


def reject_empty(csv: CSVIterator) -> CSVIterator:
    first = next(csv, None)
    if first is None:
        raise CSVParseError("CSV cannot be empty.")
    second = next(csv, None)
    if second is None:
        raise CSVParseError("CSV must contain at least one row after headers.")
    return itertools.chain([first, second], csv)


def validate_headers(csv: CSVIterator, columns: CSVColumnTypes) -> CSVIterator:
    headers = next(csv)

    # Count empty trailing columns so we can ignore them.
    empty_trailing_header_count = 0
    for header in reversed(headers):
        if len(header) == 0:
            empty_trailing_header_count += 1
        else:
            break
    if empty_trailing_header_count > 0:
        headers = headers[0:-empty_trailing_header_count]

    lowercase_headers = [header.lower() for header in headers]

    allowed_headers = [name for (name, _type, _required) in columns]
    required_headers = [name for (name, _type, required) in columns if required]

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

    if empty_trailing_header_count == 0:
        # No empty trailing columns, just send the data through as-is.
        yield from csv
    else:
        for (row_index, row) in enumerate(csv):
            for (empty_trailing_column_index, cell) in enumerate(
                row[-empty_trailing_header_count:]
            ):
                if len(cell) > 0:
                    raise CSVParseError(
                        f"Empty trailing column {len(headers) + empty_trailing_column_index + 1} expected to have no values, but row {row_index + 1} has a value: {cell}."
                    )

            # Pass only cells for non-empty columns.
            yield row[0:-empty_trailing_header_count]


def skip_empty_rows(csv: CSVIterator) -> CSVIterator:
    for row in csv:
        if len(row) > 0 and not all(value == "" for value in row):
            yield row


def reject_empty_cells(csv: CSVIterator, columns: CSVColumnTypes) -> CSVIterator:
    headers = next(csv)
    yield headers

    for r, row in enumerate(csv):
        if len(row) != len(headers):
            raise CSVParseError(
                f"Wrong number of cells in row {r+1}."
                f" Expected {len(headers)} {pluralize('cell', len(headers))},"
                f" got {len(row)} {pluralize('cell', len(row))}."
            )
        for c, value in enumerate(row):
            [_, _, required] = columns[c]
            if required and value == "":
                raise CSVParseError(
                    "All cells must have values."
                    f" Got empty cell at column {headers[c]}, row {r+1}."
                )
        yield row


def validate_values(csv: CSVIterator, columns: CSVColumnTypes) -> CSVIterator:
    yield next(csv)  # Skip the headers
    for r, row in enumerate(csv):

        for (header, value_type, _required), value in zip(columns, row):
            where = f"column {header}, row {r+1}"

            if value_type is CSVValueType.NUMBER:
                try:
                    locale.atoi(value)
                except ValueError as error:
                    raise CSVParseError(f"Expected a number in {where}. Got: {value}.")

            if value_type is CSVValueType.EMAIL:
                if not EMAIL_REGEX.match(value):
                    raise CSVParseError(
                        f"Expected an email address in {where}. Got: {value}."
                    )

        yield row


def convert_rows_to_dicts(csv: CSVIterator, columns: CSVColumnTypes) -> CSVDictIterator:
    next(csv)  # Skip headers
    headers = [header for (header, _, _) in columns]
    return (dict(zip(headers, row)) for row in csv)


def pluralize(word: str, n: int) -> str:
    return word if n == 1 else f"{word}s"


def decode_csv_file(file: bytes) -> str:
    try:
        detect_result = chardet.detect(file)

        if detect_result["confidence"] > 0:
            try:
                return file.decode(detect_result["encoding"])
            except UnicodeDecodeError:
                pass

        return file.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise BadRequest(
            "Please submit a valid CSV."
            " If you are working with an Excel spreadsheet,"
            " make sure you export it as a .csv file before uploading"
        )
