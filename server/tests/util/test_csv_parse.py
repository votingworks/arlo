from typing import Union, List
import os, io, pytest
from werkzeug.exceptions import BadRequest
from ...api.ballot_manifest import BALLOT_MANIFEST_COLUMNS
from ...util.jurisdiction_bulk_update import JURISDICTIONS_COLUMNS
from ...util.csv_parse import (
    parse_csv,
    decode_csv_file,
    CSVParseError,
    CSVColumnType,
)


# Happy path
def test_parse_csv_happy_path():
    parsed = list(
        parse_csv(
            (
                "Batch Name,Number of Ballots\n"
                "Batch A,20\n"
                "B,4\n"
                "c1111111,100\n"
                "box 2,100000"
            ),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [
        {"Batch Name": "Batch A", "Number of Ballots": "20"},
        {"Batch Name": "B", "Number of Ballots": "4"},
        {"Batch Name": "c1111111", "Number of Ballots": "100"},
        {"Batch Name": "box 2", "Number of Ballots": "100000"},
    ]


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
        == "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Storage Location, Tabulator."
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
        == "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Storage Location, Tabulator."
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


def test_parse_csv_empty_trailing_columns_with_data_in_those_columns():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots,,\n" "Batch A,20,,z\n" ",,,\n"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )

    assert (
        str(error.value)
        == "Empty trailing column 4 expected to have no values, but row 1 has a value: z."
    )


def test_parse_csv_duplicate_value_in_unique_column():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots\n" "1,2\n" "1,3"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "Values in column Batch Name must be unique. Found duplicate value: 1."
    )


# Cases where we are lenient


def test_parse_csv_header_wrong_case():
    parsed = list(
        parse_csv(
            ("BATCH NAME,NUMBER OF BALLOTS\n" "Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"

    parsed = list(
        parse_csv(
            ("BaTcH nAmE,nUmBeR oF bAlLoTs\n" "Batch A,20\n"), BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == "20"


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
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" "Batch A,20\n" ",\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" ",\n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" "Batch A,20\n" "\n" "\n" "\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1


def test_parse_csv_empty_trailing_columns():
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots,,\n" "Batch A,20,,\n" ",,,\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [{"Batch Name": "Batch A", "Number of Ballots": "20"}]


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
        "Found unexpected columns. Allowed columns: Batch Name, Number of Ballots, Storage Location, Tabulator.",
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        """Batch Name,Number of Ballots
"Blue Lake Township, Precinct 1",485
"Casnovia Township, Precinct 1",440
"Cedar Creek Township, Precinct 1",544
"Dalton Township, Precinct 1",270
"Dalton Township, Precinct 1 AV",229
"Dalton Township, Precinct 2",225
"Dalton Township, Precinct 2 AV",75
"Ravenna Township, Precinct 1",278
"Ravenna Township, Precinct 1 AV",297
"Sullivan Township, Precinct 1",309
"Sullivan Township, Precinct 1 AV",220
"White River Township, Precinct 1",358
"Whitehall Township, Precinct 1",288
"Whitehall Township, Precinct 1",168
"Whitehall Township, Precinct 1",493
"City of Montague, Precinct 1",562
"City of Muskegon, Precinct 1",189
"City of Muskegon, Precinct 1 AV",181
"City of Whitehall, Precinct 1",495
"City of Whitehall, Precinct 1",813
""",
        "Values in column Batch Name must be unique. Found duplicate value: Whitehall Township, Precinct 1.",
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
        """BATCH NAME,NUMBER OF BALLOTS
BENONA,403
CLAYBANKS,157
COLFAX,63
CRYSTAL,100
ELBRIDGE,203
FERRY,229
GOLDEN,397
GRANT,436
GREENWOOD,164
HART,388
LEAVITT,95
NEWFIELD,471
OTTO,114
PENTWATER,523
SHELBY 1,421
SHELBY 2,198
WEARE,271
CITY OF HART,333

""",
        18,
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
    (
        """BATCH NAME,NUMBER OF BALLOTS,
BREEN,140,
BREITUNG 1,253,
BREITUNG 2,239,
BREITUNG 3,299,
BREITUNG AVCB,624,
IRON MOUNTAIN 1,329,
IRON MOUNTAIN 2,327,
IRON MOUNTAIN 3,361,
IRON MOUNTAIN AVCB,323,
KINGSFORD 1,251,
KINGSFORD 2,325,
 KINGSFORD AVCB,283,
CITY OF NORWAY 1,503,
CITY OF NORWAY AVCB,120,
FELCH,137,
NORWAY TWP 1,246,
NORWAY TWP AVCB,177,
SAGOLA,227,
WAUCEDAH 1,215,
WEST BRANCH,22,
,,
,,
,,
,,
,,
,,
,,
,,
,,
,,
,,
,,
,,
,,
""",
        20,
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        # pylint: disable=trailing-whitespace
        """Batch Name,Number of Ballots,,
Ash #1,289,,
Ash #2,251,,
Ash #3,211,,
Ash AV #1,791,,
Bedford #1,152,,
Bedford #2,221,,
Bedford #3,235,,
Bedford #4,295,,
Bedford #5,282,,
Bedford #6,373,,
Bedford #7,274,,
Bedford #8,295,,
Bedford #9,166,,
Bedford #10,181,,
Bedford #11,275,,
Bedford #12,263,,
Bedford #13,292,,
Bedford #14,220,,
Bedford AV #1,2399,,
Berlin #1,286,,
Berlin #2,340,,
Berlin #3,168,,
Berlin #4,322,,
Berlin AV #1,652,,
Dundee #1,351,,
Dundee #2,478,,
Dundee #3,517,,
Erie #1,931,,
Erie #2,552,,
Exeter #1,358,,
Exeter #2,449,,
Frenchtown #1,137,,
Frenchtown #2,196,,
Frenchtown #3,186,,
Frenchtown #4,189,,
Frenchtown #5,235,, 
Frenchtown #6,254,,
Frenchtown #7,360,,
Frenchtown #8,208,,
Frenchtown #9,142,,
Frenchtown AV #1,833,,
Frenchtown AV #2,960,,
Ida #1,404,,
Ida #2,465,,
LaSalle #1,453,,
LaSalle #2,428,,
LaSalle AV #1,416,,
London #1,541,,
Milan #1,353,,
Monroe #1,239,,
Monroe #2,173,,
Monroe #3,201,,
Monroe #4,295,,
Monroe #5,356,,
Monroe #6,262,,
Monroe AV #1,1022,,
Raisinville #1,326,,
Raisinville #2,360,,
Raisinville AV #1,653,,
Summerfield #1,497,,
Whiteford #1,245,,
Whiteford #2,212,,
Whiteford AV #1,195,,
City of Luna Pier #1,537,,
City of Milan #1,465,,
City of Monroe #1,363,,
City of Monroe #2,349,,
City of Monroe #3N,176,,
City of Monroe #3S,165,,
City of Monroe #4,498,,
City of Monroe #5,438,,
City of Monroe #6,365,,
City of Monroe AV #1,1251,,
City of Petersburg #1,203,,
""",
        74,
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        io.FileIO(
            os.path.join(os.path.dirname(__file__), "windows1252-encoded.csv")
        ).read(),
        245,
        BALLOT_MANIFEST_COLUMNS,
    ),
]


def test_parse_csv_real_world_examples():
    def do_parse(csv: Union[str, bytes], columns: List[CSVColumnType]) -> list:
        if isinstance(csv, bytes):
            csv = decode_csv_file(csv)
        return list(parse_csv(csv, columns))

    for (csv, expected_error, columns) in REAL_WORLD_REJECTED_CSVS:
        with pytest.raises(CSVParseError) as error:
            do_parse(csv, columns)
        assert str(error.value) == expected_error

    for (csv, expected_rows, columns) in REAL_WORLD_ACCEPTED_CSVS:
        parsed = do_parse(csv, columns)
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
