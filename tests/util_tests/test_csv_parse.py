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
        parse_csv("", COLUMNS)
    assert str(error) == "CSV cannot be empty"


def test_parse_csv_no_headers():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("1,2\n" "3,4"), COLUMNS)
    assert str(error) == "Missing required columns: Batch Name, Number of Ballots"


def test_parse_csv_no_rows_after_headers():
    with pytest.raises(CSVParseError) as error:
        parse_csv("Batch Name,Number of Ballots", COLUMNS)
    assert str(error) == "CSV must contain at least one row after headers"


def test_parse_csv_missing_header():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name,\n" "1,2"), COLUMNS)
    assert str(error) == "Missing required column: Number of Ballots"

    with pytest.raises(CSVParseError) as error:
        parse_csv(("\n" "1,2"), COLUMNS)
    assert str(error) == "Missing required columns: Batch Name, Number of Ballots"


def test_parse_csv_headers_out_of_order():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Number of Ballots,Batch Name\n" "1,2"), COLUMNS)
    assert (
        str(error)
        == "Columns out of order. Expected order: Batch Name, Number of Ballots"
    )


def test_parse_csv_wrong_data_type():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name,Number of Ballots\n" "1,not a number"), COLUMNS)
    assert (
        str(error)
        == "Expected a number in column Number of Ballots, row 1. Got: not a number"
    )


# TODO test email validation


def test_parse_csv_empty_cell_in_column():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name,Number of Ballots\n" "1,"), COLUMNS)
    assert str(error) == "Cell cannot be empty in column Number of Ballots, row 1."


def test_parse_csv_empty_column():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name,Number of Ballots\n" "1,\n" "2,"), COLUMNS)
    assert str(error) == "Cell cannot be empty in column Number of Ballots, row 1."


def test_parse_csv_extra_column():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name,Xtra,Number of Ballots\n" "1,,2\n" "2,3,"), COLUMNS)
    assert (
        str(error)
        == "Found extra column Xtra. Expected columns: Batch Name, Number of Ballots"
    )

    with pytest.raises(CSVParseError) as error:
        parse_csv(
            ("Batch Name,Xtra,Number of Ballots,Another one\n" "1,,2,\n" "2,3,,"),
            COLUMNS,
        )
    assert (
        str(error)
        == "Found extra column Xtra. Expected columns: Batch Name, Number of Ballots"
    )


def test_parse_csv_not_comma_delimited():
    with pytest.raises(CSVParseError) as error:
        parse_csv(("Batch Name\tNumber of Ballots\n" "1\t2\n"), COLUMNS)
    assert str(error) == "CSV must be comma-delimited, not tab-delimited."


def test_parse_csv_excel_file():
    with open("./test-ballot-manifest.xlsx", "r") as excel_file:
        with pytest.raises(CSVParseError) as error:
            parse_csv(excel_file.read(), COLUMNS)
    assert str(error) == "Please submit a CSV file, not an Excel file."


# Cases where we are lenient


def test_parse_csv_header_wrong_case():
    parsed = parse_csv(("BATCH NAME,NUMBER OF BALLOTS\n" "Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1

    parsed = parse_csv(("BaTcH nAmE,nUmBeR oF bAlLoTs\n" "Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1


def test_parse_csv_space_in_header():
    parsed = parse_csv(("Batch Name ,Number of Ballots\n" "Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1
    assert list(parsed)[0]["Batch Name"] == "Batch A"
    assert list(parsed)[0]["Number of Ballots"] == "20"

    parsed = parse_csv(
        ("   Batch Name ,  Number of Ballots \n" "Batch A,20\n"), COLUMNS,
    )
    assert len(list(parsed)) == 1
    assert list(parsed)[0]["Batch Name"] == "Batch A"
    assert list(parsed)[0]["Number of Ballots"] == "20"


def test_parse_csv_space_in_value():
    parsed = parse_csv(("Batch Name,Number of Ballots\n" " Batch A,20\n"), COLUMNS,)
    assert len(list(parsed)) == 1
    assert list(parsed)[0]["Batch Name"] == "Batch A"
    assert list(parsed)[0]["Number of Ballots"] == "20"

    parsed = parse_csv(
        ("Batch Name,Number of Ballots\n" " Batch A    ,   20   \n"), COLUMNS,
    )
    assert len(list(parsed)) == 1


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
