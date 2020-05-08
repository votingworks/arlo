import io, itertools, re, locale
from enum import Enum
from typing import List, Tuple, Iterator, Dict, Any
import csv as py_csv


class CSVParseError(Exception):
    pass


class CSVValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"


# https://emailregex.com/
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


CSVColumnTypes = List[Tuple[str, CSVValueType]]

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
    csv = reject_empty_cells(csv)
    csv = validate_values(csv, columns)
    return convert_rows_to_dicts(csv)


def validate_is_csv(csv: str):
    lines = csv.splitlines()
    if len(lines) == 0:
        raise CSVParseError("CSV cannot be empty.")

    dialect = None
    try:
        dialect = py_csv.Sniffer().sniff(lines[0], delimiters=",\t")
        if dialect.delimiter == ",":
            return
    except Exception:
        pass

    detail = ""
    if not dialect:
        pass
    elif dialect.delimiter == "\t":
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
    expected_headers = [name for [name, type] in columns]

    if len(headers) > len(columns):
        raise CSVParseError(
            f"Too many columns. Expected columns: {', '.join(expected_headers)}."
        )

    lowercase_headers = [header.lower() for header in headers]
    missing_headers = [
        expected_header
        for expected_header in expected_headers
        if expected_header.lower() not in lowercase_headers
    ]
    if len(missing_headers) > 0:
        raise CSVParseError(
            f"Missing required {pluralize('column', len(missing_headers))}:"
            f" {', '.join(missing_headers)}."
        )

    lowercase_expected_headers = [header.lower() for header in expected_headers]
    if lowercase_headers != lowercase_expected_headers:
        print(headers, expected_headers)
        raise CSVParseError(
            f"Columns out of order. Expected order: {', '.join(expected_headers)}."
        )

    return itertools.chain([headers], csv)


def skip_empty_rows(csv: CSVIterator) -> CSVIterator:
    for row in csv:
        if len(row) > 0 and not all(value == "" for value in row):
            yield row


def reject_empty_cells(csv: CSVIterator) -> CSVIterator:
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
            if value == "":
                raise CSVParseError(
                    "All cells must have values."
                    f" Got empty cell at column {headers[c]}, row {r+1}."
                )
        yield row


def convert_rows_to_dicts(csv: CSVIterator) -> CSVDictIterator:
    headers = next(csv)
    return (dict(zip(headers, row)) for row in csv)


def validate_values(csv: CSVIterator, columns: CSVColumnTypes) -> CSVIterator:
    yield next(csv)  # Skip the headers
    for r, row in enumerate(csv):

        for (header, value_type), value in zip(columns, row):
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


def pluralize(word: str, n: int) -> str:
    return word if n == 1 else f"{word}s"
