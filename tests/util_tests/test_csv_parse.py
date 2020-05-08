import pytest, os
from util.csv_parse import parse_csv, decode_csv_file, CSVParseError, CSVValueType
from werkzeug.exceptions import BadRequest

# Column names based on ballot manifest
BALLOT_MANIFEST_COLUMNS = [
    ("Batch Name", CSVValueType.TEXT, True),
    ("Number of Ballots", CSVValueType.NUMBER, True),
    ("Tabulator", CSVValueType.TEXT, False),
    ("Storage Location", CSVValueType.TEXT, False),
]

JURISDICTIONS_COLUMNS = [
    ("Jurisdiction", CSVValueType.TEXT, True),
    ("Admin Email", CSVValueType.EMAIL, True),
]

# Happy path
def test_parse_csv_happy_path():
    parsed = parse_csv(
        (
            "Batch Name,Number of Ballots\n"
            "Batch A,20\n"
            "B,4\n"
            "c1111111,100\n"
            "box 2,100000"
        ),
        BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 4


def test_parse_csv_optional_columns():
    parsed = parse_csv(
        (
            "Batch Name,Number of Ballots,Tabulator\n"
            "Batch A,20,1\n"
            "B,4,2\n"
            "c1111111,100,1\n"
            "box 2,100000,2"
        ),
        BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 4


# Cases where we are strict


def test_parse_csv_empty():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv("", BALLOT_MANIFEST_COLUMNS))
    assert str(error.value) == "CSV cannot be empty."


def test_parse_csv_no_headers():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("1,2\n" "3,4"), BALLOT_MANIFEST_COLUMNS))
    assert (
        str(error.value) == "Missing required columns: Batch Name, Number of Ballots."
    )


def test_parse_csv_no_rows_after_headers():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv("Batch Name,Number of Ballots", BALLOT_MANIFEST_COLUMNS))
    assert str(error.value) == "CSV must contain at least one row after headers."


def test_parse_csv_missing_header():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,\n" "1,2"), BALLOT_MANIFEST_COLUMNS))
    assert str(error.value) == "Missing required column: Number of Ballots."

    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("\n" "1,2"), BALLOT_MANIFEST_COLUMNS))
    assert (
        str(error.value)
        == "Please submit a valid CSV file with columns separated by commas."
    )


def test_parse_csv_headers_out_of_order():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(("Number of Ballots,Batch Name\n" "1,2"), BALLOT_MANIFEST_COLUMNS)
        )
    assert (
        str(error.value)
        == "Columns out of order. Expected order: Batch Name, Number of Ballots."
    )


def test_parse_csv_bad_number():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots\n" "1,not a number"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "Expected a number in column Number of Ballots, row 1. Got: not a number."
    )


def test_parse_csv_bad_email():
    bad_emails = ["not an email", "a@b", "@b.com", "@", "a@.com"]
    for bad_email in bad_emails:
        with pytest.raises(CSVParseError) as error:
            list(
                parse_csv(
                    ("Jurisdiction,Admin Email\n" f"J1,{bad_email}"),
                    JURISDICTIONS_COLUMNS,
                )
            )
        assert (
            str(error.value)
            == f"Expected an email address in column Admin Email, row 1. Got: {bad_email}."
        )


def test_parse_csv_empty_cell_in_column():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(("Batch Name,Number of Ballots\n" "1,"), BALLOT_MANIFEST_COLUMNS)
        )
    assert (
        str(error.value)
        == "All cells must have values. Got empty cell at column Number of Ballots, row 1."
    )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots\n" "1,\n" "2,"), BALLOT_MANIFEST_COLUMNS
            )
        )
    assert (
        str(error.value)
        == "All cells must have values. Got empty cell at column Number of Ballots, row 1."
    )


def test_parse_csv_missing_cell_in_row():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1"), BALLOT_MANIFEST_COLUMNS))
    assert (
        str(error.value)
        == "Wrong number of cells in row 1. Expected 2 cells, got 1 cell."
    )


def test_parse_csv_extra_cell_in_row():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots\n" "1,2,3"), BALLOT_MANIFEST_COLUMNS
            )
        )
    assert (
        str(error.value)
        == "Wrong number of cells in row 1. Expected 2 cells, got 3 cells."
    )


def test_parse_csv_extra_column():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Xtra,Number of Ballots\n" "1,,2\n" "2,3,"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Tabulator, Storage Location."
    )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Xtra,Number of Ballots,Another one\n" "1,,2,\n" "2,3,,"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Tabulator, Storage Location."
    )


def test_parse_csv_not_comma_delimited():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name\tNumber of Ballots\n" "1\t2\n"), BALLOT_MANIFEST_COLUMNS
            )
        )
    assert (
        str(error.value)
        == "Please submit a valid CSV file with columns separated by commas. This file has columns separated by tabs."
    )


# Cases where we are lenient


def test_parse_csv_header_wrong_case():
    parsed = parse_csv(
        ("BATCH NAME,NUMBER OF BALLOTS\n" "Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("BaTcH nAmE,nUmBeR oF bAlLoTs\n" "Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1


def test_parse_csv_space_in_header():
    parsed = list(
        parse_csv(
            ("Batch Name ,Number of Ballots\n" "Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"

    parsed = list(
        parse_csv(
            ("   Batch Name ,  Number of Ballots \n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"


def test_parse_csv_space_in_value():
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" " Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" " Batch A    ,   20   \n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1


def test_parse_csv_empty_row():
    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" "Batch A,20\n" ",\n"),
        BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" ",\n" "Batch A,20\n"),
        BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n"), BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n" "\n" "\n"),
        BALLOT_MANIFEST_COLUMNS,
    )
    assert len(list(parsed)) == 1


REAL_WORLD_REJECTED_CSVS = [
    (
        """Batch Name,,Number of Ballots,
"Bear Creek Twp, Precinct 1",,,375
"Bear Creek Twp, Precinct 2 ",,,393
"Bear Creek Twp, AVCB, Precinct 1",,,579
"Bear Creek Twp, AVCB, Precinct 2 ",,,586
Bliss Twp,,,199
Carp Lake Twp,,,214
Center Twp,,,180
""",
        "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Tabulator, Storage Location.",
        BALLOT_MANIFEST_COLUMNS,
    ),
]

REAL_WORLD_ACCEPTED_CSVS = [
    (
        """BATCH NAME,NUMBER OF BALLOTS
Algansee,289
Batavia,175
Bethel,150
Bronson Twp.,155
Butler,173
California,61
Coldwater Twp.,597
Gilead,68
Girard,318
Kinderhook,261
Matteson,252
Noble,77
Ovid,455
Quincy #1,215
Quincy #2,286
Sherwood,273
Union,438
Bronson City,192
Coldwater City #1,311
Coldwater City #2,468
Coldwater City #3,600
Coldwater City #4,307
""",
        22,
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        """Batch Name,Number of Ballots
,
Almira,998
Benzonia,499
Benzonia AVCB,518
Blaine,210
Colfax,166
Crystal Lake,471
Gilmore,280
Homestead,644
Inland,589
Joyfield,242
Lake,356
Platte,156
Weldon,169
City of Frankfort,435

""",
        14,
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        """Jurisdiction ,Admin Email
Alcona County,abc+Alcona@gmail.com
Alger County,abc+Alger@gmail.com
Allegan County,abc+Allegan@gmail.com
""",
        3,
        JURISDICTIONS_COLUMNS,
    ),
]


def test_parse_csv_real_world_examples():
    for (csv, expected_error, columns) in REAL_WORLD_REJECTED_CSVS:
        with pytest.raises(CSVParseError) as error:
            list(parse_csv(csv, columns))
        assert str(error.value) == expected_error

    for (csv, expected_rows, columns) in REAL_WORLD_ACCEPTED_CSVS:
        parsed = list(parse_csv(csv, columns))
        assert len(parsed) == expected_rows


def test_decode_excel_file():
    excel_file_path = os.path.join(
        os.path.dirname(__file__), "test-ballot-manifest.xlsx"
    )
    with open(excel_file_path, "rb") as excel_file:
        with pytest.raises(BadRequest) as error:
            decode_csv_file(excel_file.read())
        assert error.value.description == (
            "Please submit a valid CSV."
            " If you are working with an Excel spreadsheet,"
            " make sure you export it as a .csv file before uploading"
        )
