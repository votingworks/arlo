# pylint: disable=invalid-name
import csv
import sys
from collections import defaultdict

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.manifest-for-cvr <cvr-path> <manifest-path>")
        sys.exit(1)

    with open(sys.argv[1], "r") as cvr_file:
        cvr = csv.reader(cvr_file, delimiter=",")

        _election_name_row = next(cvr)
        _contest_row = next(cvr)
        _contest_choices_row = next(cvr)
        headers_and_affiliations = next(cvr)

        assert headers_and_affiliations[1] == "TabulatorNum"
        assert headers_and_affiliations[2] == "BatchId"
        assert headers_and_affiliations[3] == "RecordId"

        batch_counts = defaultdict(int)  # type: ignore

        for row in cvr:
            [_cvr_number, tabulator_number, batch_id, record_id, *_,] = row
            batch_counts[(tabulator_number, batch_id)] += 1

    with open(sys.argv[2], "w") as manifest_file:
        manifest = csv.writer(manifest_file, delimiter=",")
        manifest.writerow(["Tabulator", "Batch Name", "Number of Ballots"])
        for (tabulator_number, batch_id), count in batch_counts.items():
            manifest.writerow([tabulator_number, batch_id, count])
