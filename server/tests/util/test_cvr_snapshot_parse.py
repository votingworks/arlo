from itertools import repeat, cycle
from server.util.cvr_snapshot_parse import read_cvr_snapshots
from server.worker.tasks import UserError


def test_read_cvr_snapshot_one_entry():
    entries = list(read_cvr_snapshots(["file.csv"], [repeat("test", 5)]))
    assert entries == [("file.csv", "test")] * 5


def test_read_cvr_snapshot_two_entries_equal_length():
    entries = list(
        read_cvr_snapshots(
            ["file1.csv", "file2.csv"], [repeat("test", 3), repeat("test", 3)]
        )
    )
    assert entries == [("file1.csv", "test")] * 3


def test_read_cvr_snapshot_two_entries_earlier_snapshot_ends_sooner():
    entries = list(
        read_cvr_snapshots(
            ["file1.csv", "file2.csv"],
            [repeat("test", 1), repeat("test", 3)],
        )
    )
    assert entries == [
        ("file1.csv", "test"),
        ("file2.csv", "test"),
        ("file2.csv", "test"),
    ]


def test_read_cvr_snapshot_two_entries_earlier_snapshot_ends_later():
    try:
        iterator = read_cvr_snapshots(
            ["file1.csv", "file2.csv"],
            [repeat("test", 3), repeat("test", 1)],
        )
        next(iterator)
        next(iterator)
        raise Exception("read_cvr_snapshots should have crashed")
    except UserError as err:
        assert (
            str(err)
            == "CVR file 'file2.csv' expected to contain row 2 because previous snapshot file 'file1.csv' has it"
        )


def test_read_cvr_snapshot_mismatched_row():
    try:
        list(
            read_cvr_snapshots(
                ["file1.csv", "file2.csv"],
                [repeat("hello", 2), cycle(["hello", "world"])],
            )
        )
    except UserError as err:
        assert (
            str(err)
            == "CVR file 'file2.csv' does not match previous snapshot file 'file1.csv' at row 2"
        )


def test_read_cvr_snapshot_many_entries_happy_path():
    entries = list(
        read_cvr_snapshots(
            ["file1.csv", "file2.csv", "file3.csv", "file4.csv", "file5.csv"],
            [
                repeat("test", 0),
                repeat("test", 1),
                repeat("test", 4),
                repeat("test", 4),
                repeat("test", 9),
            ],
        )
    )
    assert len(entries) == 9


def test_read_cvr_snapshot_malformed_iterator():
    try:
        list(
            read_cvr_snapshots(
                ["file1.csv", "file2.csv"], [cycle(["test", None]), repeat("test", 4)]
            )
        )
        raise Exception("read_cvr_snapshots should have crashed")
    except Exception as err:
        assert (
            str(err)
            == "Once an iterator for file 'file1.csv' (index 1/2) returns None for a row, it must return None for all subsequent rows."
        )
