import csv
import io
import itertools
import secrets
from typing import IO

from ..worker.tasks import UserError

# Backed by os.urandom, unlike the default random module
random = secrets.SystemRandom()

UTF8_BOM = b"\xef\xbb\xbf"
# UTF-32 LE's BOM (ff fe 00 00) starts with UTF-16 LE's
UTF16_AND_UTF32_BOMS = (b"\xfe\xff", b"\xff\xfe", b"\x00\x00\xfe\xff")


def shuffle_csv_rows(
    input_file: IO[bytes],
    output_file: IO[bytes],
    num_rows_to_skip: int = 0,
    chunk_size: int = 100,
) -> None:
    """
    Writes a copy of a CSV to output_file with the data rows (all rows after
    the header row) shuffled using a cryptographically secure source of
    randomness. To keep memory usage bounded, rows are shuffled within
    consecutive chunks of chunk_size rows rather than across the whole file.

    Rows are parsed and rewritten with the csv module, so every value is
    preserved, but quoting and line endings may change. Assumes an
    ASCII-compatible encoding (e.g., UTF-8 or Windows-1252). Raises for UTF-16
    and UTF-32 files with a byte order mark, which shuffling would corrupt.

    num_rows_to_skip is the number of rows above the header row.
    """
    assert chunk_size > 0

    start = input_file.read(4)
    # Every UTF-16 or UTF-32 character is multiple bytes, so splitting rows at
    # single-byte newlines would scramble the file
    if start.startswith(UTF16_AND_UTF32_BOMS):
        raise UserError(
            "UTF-16- and UTF-32-encoded CSV files aren't supported. Please save the file as UTF-8 and upload it again."
        )
    # Copy a UTF-8 BOM through as is, so it stays at the very start of the file
    if start.startswith(UTF8_BOM):
        output_file.write(UTF8_BOM)
        input_file.seek(len(UTF8_BOM))
    else:
        input_file.seek(0)

    # Decode as Latin-1 rather than UTF-8 since we don't know the file's
    # encoding (it may be Windows-1252). Latin-1 maps every byte to a character
    # and back, so values round trip byte for byte, and the bytes the csv
    # module cares about (comma, quote, newline) mean the same thing in any
    # ASCII-compatible encoding.
    text_input = io.TextIOWrapper(input_file, encoding="latin-1", newline="")
    text_output = io.TextIOWrapper(output_file, encoding="latin-1", newline="")
    try:
        reader = csv.reader(text_input)
        writer = csv.writer(text_output)
        writer.writerows(itertools.islice(reader, num_rows_to_skip + 1))
        # Make the first chunk a random size smaller than chunk_size, so that
        # chunk boundaries vary and the last chunk isn't always a fixed size
        # (e.g., a single row that never moves when there are 101 rows)
        first_chunk = list(itertools.islice(reader, random.randrange(chunk_size)))
        random.shuffle(first_chunk)
        writer.writerows(first_chunk)
        while chunk := list(itertools.islice(reader, chunk_size)):
            random.shuffle(chunk)
            writer.writerows(chunk)
        text_output.flush()
    finally:
        # Detach so that the wrappers don't close the underlying files
        text_input.detach()
        text_output.detach()
