import pytest
from util.csv_parse import parse_csv, CSVParseError, CSVValueType

# Column names based on ballot manifest
COLUMNS = [
    ("Batch Name", CSVValueType.TEXT),
    ("Number of Ballots", CSVValueType.NUMBER),
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
        COLUMNS,
    )
    assert len(list(parsed)) == 4


# Cases where we are strict


def test_parse_csv_empty():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv("", COLUMNS))
    assert str(error.value) == "CSV cannot be empty"


def test_parse_csv_no_headers():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("1,2\n" "3,4"), COLUMNS))
    assert str(error.value) == "Missing required columns: Batch Name, Number of Ballots"


def test_parse_csv_no_rows_after_headers():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv("Batch Name,Number of Ballots", COLUMNS))
    assert str(error.value) == "CSV must contain at least one row after headers"


def test_parse_csv_missing_header():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,\n" "1,2"), COLUMNS))
    assert str(error.value) == "Missing required column: Number of Ballots"

    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("\n" "1,2"), COLUMNS))
    assert (
        str(error.value)
        == "Please submit a valid CSV file with columns separated by commas."
    )


def test_parse_csv_headers_out_of_order():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Number of Ballots,Batch Name\n" "1,2"), COLUMNS))
    assert (
        str(error.value)
        == "Columns out of order. Expected order: Batch Name, Number of Ballots"
    )


def test_parse_csv_duplicate_header():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots,Batch Name\n" "1,2,3"), COLUMNS))
    assert (
        str(error.value)
        == "Too many columns. Expected columns: Batch Name, Number of Ballots"
    )


def test_parse_csv_bad_number():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1,not a number"), COLUMNS))
    assert (
        str(error.value)
        == "Expected a number in column Number of Ballots, row 1. Got: not a number"
    )


def test_parse_csv_bad_email():
    bad_emails = ["not an email", "a@b", "@b.com", "@", "a@.com"]
    for bad_email in bad_emails:
        with pytest.raises(CSVParseError) as error:
            list(
                parse_csv(
                    ("Jurisdiction,Admin Email\n" f"J1,{bad_email}"),
                    [
                        ("Jurisdiction", CSVValueType.TEXT),
                        ("Admin Email", CSVValueType.EMAIL),
                    ],
                )
            )
        assert (
            str(error.value)
            == f"Expected an email address in column Admin Email, row 1. Got: {bad_email}"
        )


def test_parse_csv_empty_cell_in_column():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1,"), COLUMNS))
    assert (
        str(error.value)
        == "All cells must have values. Got empty cell at column Number of Ballots, row 1."
    )

    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1,\n" "2,"), COLUMNS))
    assert (
        str(error.value)
        == "All cells must have values. Got empty cell at column Number of Ballots, row 1."
    )


def test_parse_csv_missing_cell_in_row():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1"), COLUMNS))
    assert (
        str(error.value)
        == "Wrong number of cells in row 1. Expected 2 cells, got 1 cell."
    )


def test_parse_csv_extra_cell_in_row():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1,2,3"), COLUMNS))
    assert (
        str(error.value)
        == "Wrong number of cells in row 1. Expected 2 cells, got 3 cells."
    )


def test_parse_csv_extra_column():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(("Batch Name,Xtra,Number of Ballots\n" "1,,2\n" "2,3,"), COLUMNS)
        )
    assert (
        str(error.value)
        == "Too many columns. Expected columns: Batch Name, Number of Ballots"
    )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Xtra,Number of Ballots,Another one\n" "1,,2,\n" "2,3,,"),
                COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "Too many columns. Expected columns: Batch Name, Number of Ballots"
    )


def test_parse_csv_not_comma_delimited():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name\tNumber of Ballots\n" "1\t2\n"), COLUMNS))
    assert (
        str(error.value)
        == "Please submit a valid CSV file with columns separated by commas. This file has columns separated by tabs."
    )


# def test_parse_csv_excel_file():
#     excel_file_path = os.path.join(
#         os.path.dirname(__file__), "test-ballot-manifest.xlsx"
#     )
#     with open(excel_file_path, "r") as excel_file:
#         with pytest.raises(CSVParseError) as error:
#             list(parse_csv(excel_file.read().decode("utf-8-sig"), COLUMNS))
#     assert str(error.value) == (
#         "Please submit a valid CSV file with columns separated by commas."
#         " If you are working with an Excel spreadsheet, make sure you export it as a CSV."
#     )


# Cases where we are lenient


def test_parse_csv_header_wrong_case():
    parsed = parse_csv(("BATCH NAME,NUMBER OF BALLOTS\n" "Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1

    parsed = parse_csv(("BaTcH nAmE,nUmBeR oF bAlLoTs\n" "Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1


def test_parse_csv_space_in_header():
    parsed = list(
        parse_csv(("Batch Name ,Number of Ballots\n" "Batch A,20\n"), COLUMNS,)
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"

    parsed = list(
        parse_csv(("   Batch Name ,  Number of Ballots \n" "Batch A,20\n"), COLUMNS,)
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"


def test_parse_csv_space_in_value():
    parsed = list(
        parse_csv(("Batch Name,Number of Ballots\n" " Batch A,20\n"), COLUMNS,)
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" " Batch A    ,   20   \n"), COLUMNS,
        )
    )
    assert len(parsed) == 1


def test_parse_csv_empty_row():
    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" "Batch A,20\n" ",\n"), COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" ",\n" "Batch A,20\n"), COLUMNS,
    )
    assert len(list(parsed)) == 1

    parsed = parse_csv(("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n"), COLUMNS,)
    assert len(list(parsed)) == 1

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n" "\n" "\n"), COLUMNS,
    )
    assert len(list(parsed)) == 1


# Real-world CSVs
# TODO
