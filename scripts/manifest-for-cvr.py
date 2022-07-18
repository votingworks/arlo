# pylint: disable=invalid-name
import re
import csv
import sys
from collections import defaultdict

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python -m scripts.manifest-for-cvr <cvr-path> <cvr-file-type> <manifest-path>"
        )
        sys.exit(1)

    cvr_file_type = sys.argv[2]
    with open(sys.argv[1], "r") as cvr_file:
        if cvr_file_type == "ESS":
            # We've seen malformed ballots CSVs to lack of field quoting, leading to
            # commas in field values being parsed as extra columns. To hackily work
            # around this, we find and quote the example of this we've seen.
            overvote_misquoting_regex = re.compile(r", Overvote,,")
            cvr_file_lines = (
                re.sub(overvote_misquoting_regex, '," Overvote,",', line)
                for line in cvr_file
            )
        else:
            cvr_file_lines = (line for line in cvr_file)

        cvr = csv.reader(cvr_file_lines, delimiter=",")
        batch_counts = defaultdict(int)  # type: ignore

        if cvr_file_type == "DOMINION":
            _election_name_row = next(cvr)
            _contest_row = next(cvr)
            _contest_choices_row = next(cvr)
            headers_and_affiliations = next(cvr)

            assert headers_and_affiliations[1] == "TabulatorNum"
            assert headers_and_affiliations[2] == "BatchId"
            assert headers_and_affiliations[3] == "RecordId"

            for row in cvr:
                [_cvr_number, tabulator_number, batch_id, _record_id, *_,] = row
                batch_counts[(tabulator_number, batch_id)] += 1

        elif cvr_file_type == "CLEARBALLOT":
            headers = next(cvr)
            first_contest_column = next(
                i for i, header in enumerate(headers) if header.startswith("Choice_")
            )
            for row in cvr:
                [
                    _row_number,
                    box_id,
                    _box_position,
                    _ballot_id,
                    _precinct_id,
                    _ballot_style_id,
                    _precinct_style_name,
                    scan_computer_name,
                    *_,
                ] = row[:first_contest_column]
                batch_counts[(scan_computer_name, box_id)] += 1

        # Expects type 2 ES&S ballots file (more on this in server/api/cvrs.py)
        elif cvr_file_type == "ESS":
            headers = next(cvr)
            header_indices = {header: i for i, header in enumerate(headers)}
            for row in cvr:
                tabulator = row[header_indices["Machine"]]
                batch_name = row[header_indices["Batch"]]
                batch_counts[(tabulator, batch_name)] += 1

    with open(sys.argv[3], "w") as manifest_file:
        manifest = csv.writer(manifest_file, delimiter=",")
        manifest.writerow(["Tabulator", "Batch Name", "Number of Ballots"])
        for (tabulator_number, batch_id), count in batch_counts.items():
            manifest.writerow([tabulator_number, batch_id, count])
