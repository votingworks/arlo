# pylint: disable=invalid-name
import sys
import os
import csv
from xml.etree import ElementTree
from collections import defaultdict

from server.util.csv_parse import get_header_indices, column_value
from server.api.cvrs import read_ess_ballots_file

# This script that parses hart CVRS and outputs a CSV file similar to the dominion format.
# Run with:
# FLASK_ENV=development poetry run python -m scripts.parse-xml-cvrs <path/to/hart/cvrs> <output-file.csv> [--include-votes-cast-per-contest] [--cvrs-include-scanned-ballot-info] [--cvrs-exported-by-tabulator]
##

# Annoyingly, ElementTree requires that you specify the namespace in all tag
# searches, so we make some wrapper functions
ns = "http://tempuri.org/CVRDesign.xsd"

def find(xml, tag):
    return xml.find(tag, namespaces={"": ns})


def findall(xml, tag):
    return xml.findall(tag, namespaces={"": ns})


NUM_CAST = "# Number of Votes Cast in Contest"
FILTER_NAME = "State Senator 18th Legislative District"


def get_directory_name(file_path):
    directory_path = os.path.dirname(file_path)
    directory_name = os.path.basename(directory_path)
    return directory_name


def parse_scanned_ballot_file(file_path, cvr_workstation_mapping):
    with open(file_path, "r", encoding="utf-8") as ballots_file:
        headers, rows = read_ess_ballots_file(ballots_file)
        if "CvrId" not in headers or "Workstation" not in headers:
            return None

        header_indices = get_header_indices(headers)

        for row_index, row in enumerate(rows):
            cvr_number = column_value(row, "CvrId", row_index + 1, header_indices)
            workstation = column_value(
                row, "Workstation", row_index + 1, header_indices
            )
            cvr_workstation_mapping[cvr_number] = workstation
        return cvr_workstation_mapping


def parse_cvr_file(
    file_path,
    use_directory_name_as_tabulator=False,
    include_votes_cast_per_contest=False,
):
    xml = ElementTree.parse(file_path).getroot()
    assert xml.tag == f"{{{ns}}}Cvr"

    cvr = {
        "CvrGuid": find(xml, "CvrGuid").text,
        "BatchNumber": find(xml, "BatchNumber").text,
        "BatchSequence": find(xml, "BatchSequence").text,
        "SheetNumber": find(xml, "SheetNumber").text,
        "PrecinctSplitName": find(find(xml, "PrecinctSplit"), "Name").text,
        "PrecinctSplitId": find(find(xml, "PrecinctSplit"), "Id").text,
        # { contest: { choice: vote }}
        "Contests": defaultdict(dict),
    }

    for contest in findall(find(xml, "Contests"), "Contest"):
        contest_name = find(contest, "Name").text
        choices = findall(find(contest, "Options"), "Option")
        num_votes_made_in_contest = len(choices)
        if include_votes_cast_per_contest:
            cvr["Contests"][contest_name][NUM_CAST] = num_votes_made_in_contest
        for choice in choices:
            if find(choice, "WriteInData"):
                choice_name = "WRITE-IN"
            else:
                choice_name = find(choice, "Name").text
            vote = find(choice, "Value").text
            cvr["Contests"][contest_name][choice_name] = vote

    if use_directory_name_as_tabulator:
        cvr["Tabulator"] = get_directory_name(file_path)

    return cvr


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 6:
        print(
            "Usage: python -m scripts.parse-xml-cvrs <cvr_directory_path> <output_csv_path> [--cvrs-exported-by-tabulator] [--include-votes-cast-per-contest] [--cvrs-include-scanned-ballot-info]",
            file=sys.stderr,
        )
        sys.exit(1)

    cvr_directory_path = sys.argv[1]
    output_csv_path = sys.argv[2]
    cvrs_exported_by_tabulator = False
    include_votes_cast_per_contest = False
    cvrs_include_scanned_ballot_info = False
    for arg in sys.argv[3:]:
        if arg == "--cvrs-exported-by-tabulator":
            cvrs_exported_by_tabulator = True
        if arg == "--cvrs-include-scanned-ballot-info":
            cvrs_include_scanned_ballot_info = True
        elif arg == "--include-votes-cast-per-contest":
            include_votes_cast_per_contest = True
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            print(
                "Usage: python -m scripts.parse-xml-cvrs <cvr_directory_path> <output_csv_path> [--cvrs-exported-by-tabulator] [--include-votes-cast-per-contest]",
                file=sys.stderr,
            )
            sys.exit(1)

    print("Finding CVR files...")

    cvr_file_paths = []
    scanned_ballot_file_paths = []
    if cvrs_exported_by_tabulator or cvrs_include_scanned_ballot_info:
        for entry in os.scandir(cvr_directory_path):
            if entry.is_dir():
                for sub_entry in os.scandir(entry.path):
                    if sub_entry.is_file() and sub_entry.name.endswith(".xml"):
                        cvr_file_paths.append(sub_entry.path)
            if (
                cvrs_include_scanned_ballot_info
                and entry.is_file()
                and entry.name.endswith(".csv")
            ):
                scanned_ballot_file_paths.append(entry.path)
    else:
        for entry in os.scandir(cvr_directory_path):
            if entry.is_file() and entry.name.endswith(".xml"):
                cvr_file_paths.append(entry.path)

    print(f"Found {len(cvr_file_paths)} CVR files")

    cvrs = []
    contest_choices: dict = defaultdict(set)
    for cvr_file_path in cvr_file_paths:
        try:
            cvr = parse_cvr_file(
                cvr_file_path,
                use_directory_name_as_tabulator=cvrs_exported_by_tabulator,
                include_votes_cast_per_contest=include_votes_cast_per_contest,
            )
        except Exception as exc:
            print(f"Error parsing file: {cvr_file_path}")
            raise exc

        cvrs.append(cvr)

        # Keep track of all contest choices we've seen
        for contest_name, choices in cvr["Contests"].items():
            for choice_name in choices:
                contest_choices[contest_name].add(choice_name)

        if len(cvrs) % 1000 == 0:
            print(f"Parsed {len(cvrs)} files")

    print("Parsing ballot information files...")
    cvr_workstation_mapping: dict = {}
    for scanned_ballot_path in scanned_ballot_file_paths:
        try:
            cvr = parse_scanned_ballot_file(
                scanned_ballot_path,
                cvr_workstation_mapping,
            )
        except Exception as exc:
            print(f"Error parsing file: {scanned_ballot_path}")
            raise exc

    print("Writing CSV...")

    contest_choice_pairs = []
    filtered_contest_name = ""
    for contest_name, choices in contest_choices.items():
        contest_name_cleaned = contest_name.replace("\n", " ")
        if contest_name_cleaned != FILTER_NAME:
            continue
        filtered_contest_name = contest_name
        for choice_name in choices:
            if choice_name != NUM_CAST:
                contest_choice_pairs.append((contest_name, choice_name))
        if include_votes_cast_per_contest:
            contest_choice_pairs.append((contest_name, NUM_CAST))

    with open(output_csv_path, "w", encoding="utf8") as output_file:

        writer = csv.writer(output_file)
        writer.writerow(["Election Name", "0.00.0.00"])

        contest_headers = ["", "", "", "", "", "", ""] + [
            f"{contest_name}" for contest_name, _ in contest_choice_pairs
        ]
        writer.writerow(contest_headers)

        choice_headers = ["", "", "", "", "", "", ""] + [
            choice_name for _, choice_name in contest_choice_pairs
        ]
        writer.writerow(choice_headers)

        headers = [
            "CvrNumber",
            "BatchNumber",
            "BatchSequence",
            "ImprintedId",
            "PrecinctSplit Name",
            "PrecinctSplit Id",
            "Workstation",
        ] + ["NP" for _ in contest_choice_pairs]
        writer.writerow(headers)

        for i, cvr in enumerate(cvrs):
            if filtered_contest_name not in cvr["Contests"]:
                continue
            if cvr["Contests"][filtered_contest_name][NUM_CAST] != 0:
                continue
            row = [
                i,
                cvr["BatchNumber"],
                cvr["BatchSequence"],
                cvr["CvrGuid"],
                cvr["PrecinctSplitName"],
                cvr["PrecinctSplitId"],
            ]
            if cvr["CvrGuid"] in cvr_workstation_mapping:
                row.append(cvr_workstation_mapping[cvr["CvrGuid"]])
            else:
                row.append("")

            # Fill in missing contest choices with 0s
            for contest_name, choice_name in contest_choice_pairs:
                if contest_name not in cvr["Contests"]:
                    row.append("")
                elif choice_name not in cvr["Contests"][contest_name]:
                    row.append(0)
                else:
                    row.append(cvr["Contests"][contest_name][choice_name])

            writer.writerow(row)
