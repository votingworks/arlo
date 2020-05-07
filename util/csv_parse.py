import io
from enum import Enum
from typing import List, Tuple, Iterable
from csv import reader, Dialect


class CSVParseError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class CSVValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"


CSVRow = List[str]
CSVIterator = Iterable[CSVRow]

# Robust CSV parsing
# "Be conservative in what you do, be liberal in what you accept from others"
# https://en.wikipedia.org/wiki/Robustness_principle
def parse_csv(csv_string: str, columns: List[Tuple[str, CSVValueType]]) -> CSVIterator:
    csv = reader(io.StringIO(csv_string), delimiter=",")
    csv = strip_whitespace(csv)
    csv = convert_rows_to_dicts(csv)
    return csv


def strip_whitespace(csv: CSVIterator) -> CSVIterator:
    return ([cell.strip() for cell in row] for row in csv)


def convert_rows_to_dicts(csv: CSVIterator) -> CSVIterator:
    headers = next(csv, None)
    if not headers:
        raise CSVParseError("CSV cannot be empty")
    return (dict(zip(headers, row)) for row in csv)
