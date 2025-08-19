import itertools
from typing import Iterator, List, Tuple, TypeVar

import logging
from server.worker.tasks import UserError

T = TypeVar("T")

logger = logging.getLogger("arlo.cvr_snapshot_parsing")


def read_cvr_snapshots(
    file_names: List[str], row_iterators: List[Iterator[T]]
) -> Iterator[Tuple[str, T]]:
    """Reads all rows from CVR snapshots with the expectation that later snapshots
    contain all rows from earlier snapshots. The this function yields tuples
    pairing a row with the name of the file that row first appears in.
    """
    max_completed_snapshot_file_index = -1

    logger.info(f"Reading snapshot from files: {file_names}")

    for row_index, rows in enumerate(itertools.zip_longest(*row_iterators)):
        last_row = None
        first_file_containing_row = None

        for file_index, row in enumerate(rows):
            if row is None:
                if last_row is not None:
                    logger.error(
                        f"Row is missing in snapshot file {file_names[file_index]} ({file_index}) but exists in previous snapshot file {file_names[file_index - 1]} ({file_index - 1})"
                    )
                    raise UserError(
                        f"CVR file '{file_names[file_index]}' expected to contain row {row_index + 1} because previous snapshot file '{file_names[file_index - 1]}' has it"
                    )
                if file_index > max_completed_snapshot_file_index:
                    max_completed_snapshot_file_index = file_index
            else:
                assert file_index > max_completed_snapshot_file_index, (
                    f"None-returning row iterator ({file_index + 1}/{len(row_iterators)}, '{file_names[file_index]}') must always return None thereafter"
                )
                if first_file_containing_row is None:
                    first_file_containing_row = file_names[file_index]

            if row is not None and last_row is not None and row != last_row:
                raise UserError(
                    f"CVR file '{file_names[file_index]}' does not match previous snapshot file '{file_names[file_index - 1]}' at row {row_index + 1}"
                )

            last_row = row

        if last_row is None:
            break

        assert first_file_containing_row is not None
        yield (first_file_containing_row, last_row)
