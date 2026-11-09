import csv
import io

import pytest

from ...util.csv_shuffle import shuffle_csv_rows
from ...worker.tasks import UserError

HEADER_ROWS = [["a"], ["b"], ["c"], ["CvrNumber", "RecordId", "BatchId"]]
DATA_ROWS = [[str(i), str(i), f"BATCH{i}"] for i in range(50)]


def to_csv(rows: list[list[str]]) -> bytes:
    text = io.StringIO()
    csv.writer(text).writerows(rows)
    return text.getvalue().encode()


def parse(contents: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(contents.decode("latin-1"), newline="")))


def shuffle(contents: bytes, num_rows_to_skip: int = 3, chunk_size: int = 100) -> bytes:
    output = io.BytesIO()
    shuffle_csv_rows(io.BytesIO(contents), output, num_rows_to_skip, chunk_size)
    return output.getvalue()


def test_shuffles_data_rows_and_leaves_header_rows_in_place():
    output = parse(shuffle(to_csv(HEADER_ROWS + DATA_ROWS)))
    assert output[:4] == HEADER_ROWS
    assert sorted(output[4:]) == sorted(DATA_ROWS)
    assert output[4:] != DATA_ROWS


@pytest.mark.parametrize("chunk_size", [1, 7, 50, 1000])
def test_only_shuffles_rows_within_each_chunk(chunk_size):
    output = parse(shuffle(to_csv(HEADER_ROWS + DATA_ROWS), chunk_size=chunk_size))
    shuffled_rows = output[4:]
    assert sorted(shuffled_rows) == sorted(DATA_ROWS)
    # Chunk boundaries are randomly offset, but rows never leave their chunk
    for new_index, row in enumerate(shuffled_rows):
        assert abs(new_index - int(row[0])) < chunk_size
    if chunk_size == 1:
        assert shuffled_rows == DATA_ROWS


def test_moves_a_lone_last_row():
    # Without randomly offsetting chunks, the 101st row would always be alone
    # in the last chunk and never move
    data_rows = [[str(i)] for i in range(101)]
    contents = to_csv(HEADER_ROWS + data_rows)
    last_row_positions = {
        parse(shuffle(contents))[4:].index(["100"]) for _ in range(50)
    }
    assert last_row_positions != {100}


def test_num_rows_to_skip():
    header = ["CvrNumber", "BatchId"]
    output = parse(shuffle(to_csv([header] + DATA_ROWS), num_rows_to_skip=0))
    assert output[0] == header
    assert sorted(output[1:]) == sorted(DATA_ROWS)


@pytest.mark.parametrize(
    "contents",
    [
        # Quoted newlines, in both the header (like Dominion's contest names)
        # and data rows
        b'a\n"Contest 1\n(Vote For=1)",x\nc\nCvrNumber,Choice\n1,"multi\nline"\n2,3\n',
        # Stray quotes inside unquoted fields
        b'a\nb\nc\nh1,h2,h3\n1,ab"c,2\n3,4,5\n6,abc"\n7,8,9\n',
        # Dominion's leading equal signs
        b'a\nb\nc\nh1,h2\n="1",="2"\n="3",="4"\n',
        # Escaped quotes and text after a closing quote
        b'a\nb\nc\nh1,h2,h3\n1,"esc ""q""",2\n3,"a"b"c,4\n5,"""",""\n',
        # CRLF line endings, blank lines, and no final line ending
        b"a\r\nb\r\nc\r\nh1,h2\r\n1,2\r\n\r\n3,4",
        # Malformed: unterminated quoted field at the end of the file
        b'a\nb\nc\nh1,h2\n1,"unterminated\n2,3\n',
    ],
)
def test_preserves_values(contents):
    original = parse(contents)
    output = parse(shuffle(contents))
    assert output[:4] == original[:4]
    assert sorted(output[4:]) == sorted(original[4:])


def test_does_not_glue_rows_after_a_stray_quote():
    data_rows = [["1", 'ab"c', "BATCH1"]] + DATA_ROWS * 100
    output = parse(shuffle(to_csv(HEADER_ROWS + data_rows)))
    assert sorted(output[4:]) == sorted(data_rows)
    assert output[4:] != data_rows


def test_header_only():
    contents = to_csv(HEADER_ROWS)
    assert parse(shuffle(contents)) == HEADER_ROWS


@pytest.mark.parametrize(
    "encoding,bom",
    [
        ("utf-8", b""),
        ("utf-8", b"\xef\xbb\xbf"),
        ("windows-1252", b""),
    ],
)
def test_preserves_encoding_and_bom(encoding, bom):
    rows = [[str(i), f"Café {i}", f"BATCH{i}"] for i in range(20)]
    text = io.StringIO()
    csv.writer(text).writerows(HEADER_ROWS + rows)
    contents = bom + text.getvalue().encode(encoding)

    output = shuffle(contents)
    assert output.startswith(bom)
    decoded = list(
        csv.reader(io.StringIO(output[len(bom) :].decode(encoding), newline=""))
    )
    assert decoded[:4] == HEADER_ROWS
    assert sorted(decoded[4:]) == sorted(rows)


@pytest.mark.parametrize(
    "bom,encoding",
    [
        (b"\xff\xfe", "utf-16-le"),
        (b"\xfe\xff", "utf-16-be"),
        (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\x00\x00\xfe\xff", "utf-32-be"),
    ],
)
def test_raises_for_utf16_and_utf32(bom, encoding):
    contents = bom + to_csv(HEADER_ROWS + DATA_ROWS).decode().encode(encoding)
    output = io.BytesIO()
    with pytest.raises(UserError, match="UTF-16- and UTF-32-encoded"):
        shuffle_csv_rows(io.BytesIO(contents), output, 3)
    assert output.getvalue() == b""
