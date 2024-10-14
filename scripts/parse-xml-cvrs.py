# pylint: disable=invalid-name
import sys
import os
import csv
from xml.etree import ElementTree
from collections import defaultdict

# Annoyingly, ElementTree requires that you specify the namespace in all tag
# searches, so we make some wrapper functions
ns = "http://tempuri.org/CVRDesign.xsd"


def find(xml, tag):
    return xml.find(tag, namespaces={"": ns})


def findall(xml, tag):
    return xml.findall(tag, namespaces={"": ns})


def get_directory_name(file_path):
    directory_path = os.path.dirname(file_path)
    directory_name = os.path.basename(directory_path)
    return directory_name


def parse_cvr_file(file_path, use_directory_name_as_tabulator=False):
    xml = ElementTree.parse(file_path).getroot()
    assert xml.tag == f"{{{ns}}}Cvr"

    cvr = {
        "CvrGuid": find(xml, "CvrGuid").text,
        "BatchNumber": find(xml, "BatchNumber").text,
        "BatchSequence": find(xml, "BatchSequence").text,
        "SheetNumber": find(xml, "SheetNumber").text,
        "PrecinctSplit": find(find(xml, "PrecinctSplit"), "Name").text,
        # { contest: { choice: vote }}
        "Contests": defaultdict(dict),
    }

    for contest in findall(find(xml, "Contests"), "Contest"):
        contest_name = find(contest, "Name").text
        choices = findall(find(contest, "Options"), "Option")
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
    if not (
        len(sys.argv) == 3
        or (len(sys.argv) == 4 and sys.argv[1] == "--cvrs-exported-by-tabulator")
    ):
        print(
            "Usage: python -m scripts.parse-xml-cvrs [--cvrs-exported-by-tabulator] <cvr_directory_path> <output_csv_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    cvr_directory_path = sys.argv[len(sys.argv) - 2]
    output_csv_path = sys.argv[len(sys.argv) - 1]
    cvrs_exported_by_tabulator = len(sys.argv) == 4

    print("Finding CVR files...")

    cvr_file_paths = []
    if cvrs_exported_by_tabulator:
        for entry in os.scandir(cvr_directory_path):
            if entry.is_dir():
                for sub_entry in os.scandir(entry.path):
                    if sub_entry.is_file() and sub_entry.name.endswith(".xml"):
                        cvr_file_paths.append(sub_entry.path)
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

    print("Writing CSV...")

    contest_choice_pairs = [
        (contest_name, choice_name)
        for contest_name, choices in contest_choices.items()
        for choice_name in choices
    ]

    with open(output_csv_path, "w", encoding="utf8") as output_file:

        writer = csv.writer(output_file)
        writer.writerow(["Election Name", "0.00.0.00"])

        contest_headers = ["", "", "", "", ""] + [
            f"{contest_name} (Vote For=1)" for contest_name, _ in contest_choice_pairs
        ]
        writer.writerow(contest_headers)

        choice_headers = ["", "", "", "", ""] + [
            choice_name for _, choice_name in contest_choice_pairs
        ]
        writer.writerow(choice_headers)

        headers = [
            "CvrNumber",
            "TabulatorNum",
            "BatchId",
            "RecordId",
            "ImprintedId",
        ] + ["NP" for _ in contest_choice_pairs]
        writer.writerow(headers)

        for i, cvr in enumerate(cvrs):
            row = [
                i,
                cvr["Tabulator"] if cvrs_exported_by_tabulator else 1,
                cvr["BatchNumber"],
                cvr["BatchSequence"],
                cvr["CvrGuid"],
            ]

            # Fill in missing contest choices with 0s
            for contest_name, choice_name in contest_choice_pairs:
                if contest_name not in cvr["Contests"]:
                    row.append("")
                elif choice_name not in cvr["Contests"][contest_name]:
                    row.append(0)
                else:
                    row.append(cvr["Contests"][contest_name][choice_name])

            writer.writerow(row)
