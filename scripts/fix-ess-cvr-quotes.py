# pylint: disable=invalid-name
import sys
import re


# Splits a string based on a separator pattern containing capture groups. Then
# attaches the captured separator back onto the previous portion of the string.
def split_attach_sep(pattern, str):
    split = re.split(pattern, str)
    return ["".join(split[i : i + 2]) for i in range(0, len(split), 2)]


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python -m scripts.fix-ess-cvr-quotes file-type <in-cvr-path> <out-cvr-path>"
        )
        sys.exit(1)

    # TODO it seems like the rows still aren't ending up all the same length,
    # probably because the REP ballots are not padded with empty cells like the
    # DEM ballots (and headers) are
    with open(sys.argv[2], "r", encoding="utf8") as in_file, open(
        sys.argv[3], "w", encoding="utf8"
    ) as out_file:
        file_type = sys.argv[1]
        if file_type == "ballots":
            # In ballots files, we've seen misquoting in the Original Ballot Exception column.
            # It seems like they contain a list of values separated by a comma
            # and a space, so we look for that pattern and try to quote it.
            #
            # Example: ... Approved with Changes,Undervote, Overvote,Undervote,,Y, ...
            misquoting_regex = re.compile(r",([a-zA-Z ]+(?:, [a-zA-Z ]+)+),")
            for row in in_file:
                row = re.sub(misquoting_regex, r',"\1",', row)
                # Sub twice in case they overlap
                row = re.sub(misquoting_regex, r',"\1",', row)
                out_file.write(row)

        elif file_type == "cvr":
            for row in in_file:
                row = row.replace("\n", "")

                # Split off first 5 columns that don't have candidates
                [_, metadata_columns, contest_columns] = re.split(
                    r"(^(?:[\w \-]+,){5})", row
                )

                # Example contest_columns:
                # ,SMITH, "JOHN ""JOHNNY"" (CND0001)",,DOE, JANE (CND0002)
                # What we want:
                # "","SMITH, JOHN ""JOHNNY" (CND0001)","","DOE, JANE (CND0002)"

                # We're going to take advantage of the fact that every candidate
                # name and contest name ends with its id in parens.

                # First, put in a placeholder for empty columns that ends in a paren
                # re.sub only replaces non-overlapping occurrences, so we have to do this twice
                contest_columns = re.sub(r",,", ",EMPTY),", contest_columns)
                contest_columns = re.sub(r",,", ",EMPTY),", contest_columns)
                # Also handle the edges
                contest_columns = re.sub(r",$", ",EMPTY)", contest_columns)
                contest_columns = re.sub(r"^,", "EMPTY),", contest_columns)

                # Next, make undervotes and overvotes also end in a paren
                contest_columns = re.sub(r"undervote", "undervote)", contest_columns)
                contest_columns = re.sub(r"overvote", "overvote)", contest_columns)

                # Split on ), or )",
                candidates = split_attach_sep(r'(\))"?,', contest_columns)
                fixed_candidates = []
                for candidate in candidates:
                    # Remove any internal misquoting (e.g. "JOHN) in example above
                    candidate = candidate.replace(',"', ",")
                    # Put the empties, undervotes, and overvotes back
                    candidate = (
                        candidate.replace("EMPTY)", "")
                        .replace("undervote)", "undervote")
                        .replace("overvote)", "overvote")
                    )
                    # Properly quote
                    fixed_candidates.append('"' + candidate + '"')

                # Rejoin the row
                fixed_row = metadata_columns + ",".join(fixed_candidates)

                out_file.write(fixed_row + "\n")

        else:
            raise Exception('File type must be "ballots" or "cvr"')
