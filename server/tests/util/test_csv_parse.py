# pylint: disable=implicit-str-concat
from typing import BinaryIO, Union, List
import os, io, pytest
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import FileStorage

from ...api.jurisdictions import JURISDICTIONS_COLUMNS
from ...util.csv_parse import (
    parse_csv as parse_csv_binary,
    CSVParseError,
    CSVColumnType,
    CSVValueType,
    validate_csv_mimetype,
    does_file_have_zip_mimetype,
)

BALLOT_MANIFEST_COLUMNS = [
    CSVColumnType("Batch Name", CSVValueType.TEXT, unique=True),
    CSVColumnType("Number of Ballots", CSVValueType.NUMBER),
    CSVColumnType("Tabulator", CSVValueType.TEXT, required_column=False),
    CSVColumnType("CVR", CSVValueType.YES_NO, required_column=False),
]

BALLOT_MANIFEST_COLUMNS_COMPOSITE_KEY = [
    CSVColumnType("Batch Name", CSVValueType.TEXT, unique=True),
    CSVColumnType("Number of Ballots", CSVValueType.NUMBER),
    CSVColumnType("Tabulator", CSVValueType.TEXT, unique=True),
]


# Quick wrapper function so we can write the tests with regular strings, not byte strings
def parse_csv(csv_string: str, columns: List[CSVColumnType]):
    return parse_csv_binary(io.BytesIO(csv_string.encode("utf-8")), columns)


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
        {"Batch Name": "Batch A", "Number of Ballots": 20},
        {"Batch Name": "B", "Number of Ballots": 4},
        {"Batch Name": "c1111111", "Number of Ballots": 100},
        {"Batch Name": "box 2", "Number of Ballots": 100000},
    ]


def test_parse_csv_optional_columns():
    parsed = list(
        parse_csv(
            (
                "Batch Name,Number of Ballots,Tabulator,CVR\n"
                "Batch A,20,1,Y\n"
                "B,4,2,N\n"
                "c1111111,100,1,yes\n"
                "box 2,100000,2,no"
            ),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [
        {
            "Batch Name": "Batch A",
            "Number of Ballots": 20,
            "Tabulator": "1",
            "CVR": True,
        },
        {"Batch Name": "B", "Number of Ballots": 4, "Tabulator": "2", "CVR": False},
        {
            "Batch Name": "c1111111",
            "Number of Ballots": 100,
            "Tabulator": "1",
            "CVR": True,
        },
        {
            "Batch Name": "box 2",
            "Number of Ballots": 100000,
            "Tabulator": "2",
            "CVR": False,
        },
    ]


def test_parse_csv_allow_empty_rows():
    parsed = list(
        parse_csv(
            ("Column 1,Column 2\n" "A,\n" ",2\n" "A,1\n"),
            [
                CSVColumnType("Column 1", CSVValueType.TEXT, allow_empty_rows=True),
                CSVColumnType(
                    "Column 2",
                    CSVValueType.NUMBER,
                    required_column=False,
                    allow_empty_rows=True,
                ),
            ],
        )
    )

    assert parsed == [
        {"Column 1": "A", "Column 2": None},
        {"Column 1": None, "Column 2": 2},
        {"Column 1": "A", "Column 2": 1},
    ]


def test_parse_csv_composite_unique_key():
    parsed = parse_csv(
        (
            "Batch Name,Number of Ballots,Tabulator\n"
            "Batch A,20,1\n"
            "B,4,2\n"
            "c1111111,100,1\n"
            "box 2,100000,2"
        ),
        BALLOT_MANIFEST_COLUMNS_COMPOSITE_KEY,
    )
    assert len(list(parsed)) == 4


def test_parse_csv_no_unique_key():
    parsed = parse_csv(
        ("Column 1,Column 2\n" "A,1\n" "B,2\n" "A,1\n"),
        [
            CSVColumnType("Column 1", CSVValueType.TEXT),
            CSVColumnType("Column 2", CSVValueType.NUMBER),
        ],
    )

    assert len(list(parsed)) == 3


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


def test_parse_csv_duplicate_header():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Batch Name,Number of Ballots\n" "1,1,2"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert str(error.value) == "Column headers must be unique."


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
        == "Expected a number in column Number of Ballots, row 2. Got: not a number."
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
            == f"Expected an email address in column Admin Email, row 2. Got: {bad_email}."
        )


def test_parse_csv_bad_yes_no():
    bad_yes_nos = ["yess", "na", "1"]
    for bad_yes_no in bad_yes_nos:
        with pytest.raises(CSVParseError) as error:
            list(
                parse_csv(
                    ("Batch Name,Number of Ballots,CVR\n" f"A,1,{bad_yes_no}"),
                    BALLOT_MANIFEST_COLUMNS,
                )
            )
        assert (
            str(error.value)
            == f"Expected Y or N in column CVR, row 2. Got: {bad_yes_no}."
        )


def test_parse_csv_empty_cell_in_column():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(("Batch Name,Number of Ballots\n" "1,"), BALLOT_MANIFEST_COLUMNS)
        )
    assert (
        str(error.value)
        == "A value is required for the cell at column Number of Ballots, row 2."
    )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots\n" "1,\n" "2,"), BALLOT_MANIFEST_COLUMNS
            )
        )
    assert (
        str(error.value)
        == "A value is required for the cell at column Number of Ballots, row 2."
    )

    # If a non-required column is present, then all its cells must have values too
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Batch Name,Number of Ballots,Tabulator\n" "1,2,"),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "A value is required for the cell at column Tabulator, row 2."
    )


def test_parse_csv_missing_cell_in_row():
    with pytest.raises(CSVParseError) as error:
        list(parse_csv(("Batch Name,Number of Ballots\n" "1"), BALLOT_MANIFEST_COLUMNS))
    assert (
        str(error.value)
        == "Wrong number of cells in row 2. Expected 2 cells, got 1 cell."
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
        == "Wrong number of cells in row 2. Expected 2 cells, got 3 cells."
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
        == "Found unexpected columns. Allowed columns: Batch Name, CVR, Number of Ballots, Tabulator."
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
        == "Found unexpected columns. Allowed columns: Batch Name, CVR, Number of Ballots, Tabulator."
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
        == "Empty trailing column 4 expected to have no values, but row 2 has a value: z."
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
        == "Each row must be uniquely identified by Batch Name. Found duplicate: 1."
    )


def test_parse_csv_duplicate_value_with_composite_unique_columns():
    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                ("Tabulator,Batch Name,Number of Ballots\n" "1,2,4\n" "1,2,3"),
                BALLOT_MANIFEST_COLUMNS_COMPOSITE_KEY,
            )
        )
    assert (
        str(error.value)
        == "Each row must be uniquely identified by ('Batch Name', 'Tabulator'). Found duplicate: ('2', '1')."
    )


def test_parse_csv_total_row():
    for total_word in [
        "Total",
        "total",
        "Totals",
        "totals",
        "Total Ballots",
        "total ballots",
        "COUNTY TOTALS",
        "subtotal",
    ]:
        with pytest.raises(CSVParseError) as error:
            list(
                parse_csv(
                    (
                        "Batch Name,Number of Ballots\n"
                        "Batch A,20\n"
                        "Batch B,30\n"
                        f"{total_word},50\n"
                    ),
                    BALLOT_MANIFEST_COLUMNS,
                )
            )
        assert (
            str(error.value)
            == "It looks like you might have a total row (row 4). Please remove this row from the CSV."
        )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                (
                    "Batch Name,Number of Ballots\n"
                    "Batch A,20\n"
                    "Batch B,30\n"
                    "Batch C,40\n"
                    "XXX,90\n"
                    ","
                ),
                BALLOT_MANIFEST_COLUMNS,
            )
        )
    assert (
        str(error.value)
        == "It looks like the last row in the CSV might be a total row. Please remove this row from the CSV."
    )

    with pytest.raises(CSVParseError) as error:
        list(
            parse_csv(
                (
                    "Batch Name,Candidate 1,Candidate 2\n"
                    "Batch A,20,10\n"
                    "Batch B,30,20\n"
                    "Batch C,40,30\n"
                    "---,90,60\n"
                ),
                [
                    CSVColumnType("Batch Name", CSVValueType.TEXT, unique=True),
                    CSVColumnType("Candidate 1", CSVValueType.NUMBER),
                    CSVColumnType("Candidate 2", CSVValueType.NUMBER),
                ],
            )
        )
        assert (
            str(error.value)
            == "It looks like the last row in the CSV might be a total row. Please remove this row from the CSV."
        )

    # Shouldn't raise an error for a column with all 0s
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" "Batch A,0\n" "Batch B,0\n" "XXX,0\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [
        {"Batch Name": "Batch A", "Number of Ballots": 0},
        {"Batch Name": "Batch B", "Number of Ballots": 0},
        {"Batch Name": "XXX", "Number of Ballots": 0},
    ]

    # Shouldn't raise an error if some but not all columns' last value looks like a total
    parsed = list(
        parse_csv(
            (
                # Candidate 2's column could mistakenly be perceived as having a total value since
                # 0 + 10 = 10
                "Batch Name,Candidate 1,Candidate 2\n"
                "Batch A,20,0\n"
                "Batch B,30,10\n"
                "Batch C,40,10\n"
            ),
            [
                CSVColumnType("Batch Name", CSVValueType.TEXT, unique=True),
                CSVColumnType("Candidate 1", CSVValueType.NUMBER),
                CSVColumnType("Candidate 2", CSVValueType.NUMBER),
            ],
        )
    )
    assert parsed == [
        {"Batch Name": "Batch A", "Candidate 1": 20, "Candidate 2": 0},
        {"Batch Name": "Batch B", "Candidate 1": 30, "Candidate 2": 10},
        {"Batch Name": "Batch C", "Candidate 1": 40, "Candidate 2": 10},
    ]


# Cases where we are lenient


def test_parse_csv_header_wrong_case():
    parsed = list(
        parse_csv(
            ("BATCH NAME,NUMBER OF BALLOTS\n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == 20

    parsed = list(
        parse_csv(
            ("BaTcH nAmE,nUmBeR oF bAlLoTs\n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == 20


def test_parse_csv_space_in_header():
    parsed = list(
        parse_csv(
            ("Batch Name ,Number of Ballots\n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == 20

    parsed = list(
        parse_csv(
            ("   Batch Name ,  Number of Ballots \n" "Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == 20


def test_parse_csv_space_in_value():
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" " Batch A,20\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Batch Name"] == "Batch A"
    assert parsed[0]["Number of Ballots"] == 20

    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" " Batch A    ,   20   \n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1


def test_parse_csv_comma_in_number():
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots\n" 'Batch A,"2,020"\n'),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert len(parsed) == 1
    assert parsed[0]["Number of Ballots"] == 2020


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


def test_parse_csv_headers_out_of_order():
    parsed = list(
        parse_csv(("Number of Ballots,Batch Name\n" "1,2"), BALLOT_MANIFEST_COLUMNS)
    )
    assert parsed == [{"Batch Name": "2", "Number of Ballots": 1}]


def test_parse_csv_headers_out_of_order_with_optional_column():
    parsed = list(
        parse_csv(
            ("Tabulator,Number of Ballots,Batch Name\n" "A,1,2"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [{"Batch Name": "2", "Number of Ballots": 1, "Tabulator": "A"}]


def test_parse_csv_empty_trailing_columns():
    parsed = list(
        parse_csv(
            ("Batch Name,Number of Ballots,,\n" "Batch A,20,,\n" ",,,\n"),
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [{"Batch Name": "Batch A", "Number of Ballots": 20}]


def test_parse_csv_excel_mac_newlines():
    parsed = list(
        parse_csv(
            "Batch Name,Number of Ballots\rBatch 1,20",
            BALLOT_MANIFEST_COLUMNS,
        )
    )
    assert parsed == [
        {"Batch Name": "Batch 1", "Number of Ballots": 20},
    ]


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
        "Found unexpected columns. Allowed columns: Batch Name, CVR, Number of Ballots, Tabulator.",
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
        "Each row must be uniquely identified by Batch Name. Found duplicate: Whitehall Township, Precinct 1.",
        BALLOT_MANIFEST_COLUMNS,
    ),
    (
        """BATCH NAME,NUMBER OF BALLOTS
1-BELLEFONTE NORTH,227
2-BELLEFONTE NORTHEAST,384
3-BELLEFONTE SOUTH,231
4-BELLEFONTE SOUTHEAST,373
5-BELLEFONTE WEST,465
6-CENTRE HALL,362
7-HOWARD BOROUGH,177
8-MILESBURG,265
9-MILLHEIM,212
10-PHILIPSBURG 1,216
11-PHILIPSBURG 2,169
12-PHILIPSBURG 3,148
13-PORT MATILDA,134
14-SNOW SHOE BOROUGH,180
15-RUSH NORTH CENTRAL,89
16-STATE COLLEGE NORTH,380
17-STATE COLLEGE NORTHEAST,279
18-STATE COLLEGE NORTHWEST,147
19-STATE COLLEGE SOUTH 1,468
20-STATE COLLEGE SOUTH 2,625
21-STATE COLLEGE SOUTHEAST,502
22-STATE COLLEGE SOUTH CENTRAL 1,149
23-STATE COLLEGE SOUTH CENTRAL 2,309
24-PSU,323
26-STATE COLLEGE EAST 3,155
29-STATE COLLEGE EAST CENTRAL 2,139
30-STATE COLLEGE EAST CENTRAL 3,73
31-STATE COLLEGE WEST 1,344
32-STATE COLLEGE WEST 2,424
34-STATE COLLEGE WEST CENTRAL 2,154
35-UNIONVILLE,77
36-BENNER NORTH,547
37-BENNER SOUTH,749
38-BOGGS EAST,275
39-BOGGS WEST,383
40-BURNSIDE,109
41-COLLEGE NORTH,"1,007"
42-COLLEGE SOUTH,848
43-COLLEGE EAST,757
44-COLLEGE WEST,220
45-CURTIN NORTH,31
46-CURTIN SOUTH,108
47-FERGUSON NORTH 1,669
48-FERGUSON NORTH 2,385
49-FERGUSON NORTHEAST 1,546
50-FERGUSON NORTHEAST 2,305
51-FERGUSON EAST,536
52-FERGUSON WEST,557
53-GREGG,611
54-HAINES,285
55-HALFMOON PROPER,312
56-HARRIS EAST,"1,114"
57-HARRIS WEST,920
58-HOWARD TOWNSHIP,252
59-HUSTON,329
60-LIBERTY,423
61-MARION,260
62-MILES EAST,184
63-MILES WEST,93
64-PATTON NORTH 1,816
65-PATTON NORTH 2,864
66-PATTON SOUTH 1,382
67-PATTON SOUTH 2,470
68-PATTON SOUTH 3,822
69-PENN,222
70-POTTER NORTH,390
71-POTTER SOUTH,661
72-RUSH NORTH,503
73-RUSH SOUTH,98
74-RUSH EAST,41
75-RUSH WEST,175
76-SNOW SHOE EAST,284
77-SNOW SHOE WEST,155
78-SPRING NORTH,593
79-SPRING SOUTH,392
80-SPRING WEST,210
81-TAYLOR,213
82-UNION,403
83-WALKER EAST,393
84-WALKER WEST,825
85-WORTH,213
86-SPRING EAST,449
87-SPRING SOUTHWEST,435
88-FERGUSON NORTH 3,505
89-FERGUSON WEST CENTRAL,612
90-HALFMOON EAST CENTRAL,496
91-FERGUSON NORTH CENTRAL,373
Totals,"32,990"
""",
        "It looks like you might have a total row (row 89). Please remove this row from the CSV.",
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
        io.FileIO(os.path.join(os.path.dirname(__file__), "windows1252-encoded.csv")),
        245,
        BALLOT_MANIFEST_COLUMNS,
    ),
]


def test_parse_csv_real_world_examples():
    def do_parse(csv: Union[str, BinaryIO], columns: List[CSVColumnType]) -> list:
        if isinstance(csv, str):
            return list(parse_csv(csv, columns))
        return list(parse_csv_binary(csv, columns))

    for csv, expected_error, columns in REAL_WORLD_REJECTED_CSVS:
        with pytest.raises(CSVParseError) as error:
            do_parse(csv, columns)
        assert str(error.value) == expected_error

    for csv, expected_rows, columns in REAL_WORLD_ACCEPTED_CSVS:
        parsed = do_parse(csv, columns)
        assert len(parsed) == expected_rows


def test_does_file_have_zip_mimetype():
    assert does_file_have_zip_mimetype(FileStorage(b"", content_type="application/zip"))
    assert does_file_have_zip_mimetype(
        FileStorage(b"", content_type="application/x-zip-compressed")
    )
    assert not does_file_have_zip_mimetype(FileStorage(b"", content_type="text/csv"))


def test_validate_csv_mimetype():
    validate_csv_mimetype(FileStorage(b"", content_type="text/csv"))
    validate_csv_mimetype(FileStorage(b"", content_type="application/vnd.ms-excel"))

    for invalid_mimetype in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
        "text/plain",
    ]:
        with pytest.raises(BadRequest) as error:
            validate_csv_mimetype(
                FileStorage(
                    b"",
                    content_type=invalid_mimetype,
                )
            )
            assert error.value.description == (
                "Please submit a valid CSV."
                " If you are working with an Excel spreadsheet,"
                " make sure you export it as a .csv file before uploading."
            )


def test_parse_csv_excel_file():
    excel_file_path = os.path.join(
        os.path.dirname(__file__), "test-ballot-manifest.xlsx"
    )
    with open(excel_file_path, "rb") as excel_file:
        with pytest.raises(CSVParseError) as error:
            parse_csv_binary(excel_file, [])
        assert str(error.value) == (
            "Please submit a valid CSV."
            " If you are working with an Excel spreadsheet,"
            " make sure you export it as a .csv file before uploading."
        )


def test_parse_csv_pdf_file():
    with pytest.raises(CSVParseError) as error:
        parse_csv_binary(
            io.BytesIO(
                b"%PDF-1.4\r%\xe2\xe3\xcf\xd3\r\n7222 0 obj\r<</Linearized 1/L 10747310/O 7225/E 11059/N 2320/T 10602748/H [ 616 3649]>>\rendobj\r    \r\nxref\r\n7222 16\r\n0000000016 00000 n\r\n0000004265 00000 n\r\n0000004349 00000 n\r\n0000004387 00000 n\r\n0000004657 00000 n\r\n0000004748 00000 n\r\n0000005220 00000 n\r\n0000005380 00000 n\r\n0000006551 00000 n\r\n0000007201 00000 n\r\n0000007850 00000 n\r\n0000008480 00000 n\r\n0000009139 00000 n\r\n0000009801 00000 n\r\n0000010446 00000 n\r\n0000000616 00000 n\r\n"
            ),
            [],
        )
    assert str(error.value) == (
        "Please submit a valid CSV file with columns separated by commas."
    )


def test_parse_csv_cant_detect_encoding():
    undetectable_file_path = os.path.join(os.path.dirname(__file__), "undetectable.pdf")
    with open(undetectable_file_path, "rb") as file:
        with pytest.raises(CSVParseError) as error:
            parse_csv_binary(file, [])
    assert str(error.value) == (
        "Please submit a valid CSV."
        " If you are working with an Excel spreadsheet,"
        " make sure you export it as a .csv file before uploading."
    )


def test_parse_csv_xls_mislabeled_as_csv():
    xls_mislabeled_as_csv = os.path.join(
        os.path.dirname(__file__), "xls-mislabeled-as-csv.csv"
    )
    with open(xls_mislabeled_as_csv, "rb") as file:
        with pytest.raises(CSVParseError) as error:
            parse_csv_binary(file, [])
    assert str(error.value) == (
        "Please submit a valid CSV."
        " If you are working with an Excel spreadsheet,"
        " make sure you export it as a .csv file before uploading."
        "\n\nAdditional details: Unable to decode file assuming Windows-1254 encoding"
    )


def test_parse_csv_replace_bad_chars():
    # In this case, the CSV appears to be utf-8, but deep within the file there
    # are bytes that are actually latin-1 chars and can't be decoded as utf-8.
    # In this case, the ó in the last row below. In these cases, we should just
    # replace the undecodable character to avoid a crash.
    batch_rows = "\n".join([f"Batch {i},1" for i in range(1, 5000)])
    csv_with_latin_1_char = f"""Batch Name,Number of Ballots
{batch_rows}
Batch ó,1
"""
    rows = list(
        parse_csv_binary(
            io.BytesIO(csv_with_latin_1_char.encode("latin-1")), BALLOT_MANIFEST_COLUMNS
        )
    )
    assert len(rows) == 5000
    assert rows[-1]["Batch Name"] == "Batch �"
