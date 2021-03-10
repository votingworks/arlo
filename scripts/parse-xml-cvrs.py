# pylint: disable=invalid-name
import sys
import os
import csv
from xml.etree import ElementTree
from collections import defaultdict

# Annoyingly, ElementTree requires that you put the namespace in all your
# tag names
ns = "http://tempuri.org/CVRDesign.xsd"


def find(xml, tag):
    return xml.find(tag, namespaces={"": ns})


def findall(xml, tag):
    return xml.findall(tag, namespaces={"": ns})


def parse_cvr_file(file_path):
    xml = ElementTree.parse(file_path).getroot()
    assert xml.tag == f"{{{ns}}}Cvr"

    cvr = {
        "CvrGuid": find(xml, "CvrGuid").text,
        "BatchNumber": find(xml, "BatchNumber").text,
        "BatchSequence": find(xml, "BatchSequence").text,
        "SheetNumber": find(xml, "SheetNumber").text,
        "PrecinctSplit": find(find(xml, "PrecinctSplit"), "Name").text,
        # { contest: { choice: 0 | 1 | None }}
        "Contests": defaultdict(dict),
    }

    for contest in findall(find(xml, "Contests"), "Contest"):
        contest_name = find(contest, "Name").text
        # # Undervotes should be recorded as all 0s, which is handled below
        # if find(contest, "Undervotes"):
        #     cvr["Contests"][contest_name] = {}
        #     continue

        choices = findall(find(contest, "Options"), "Option")
        for choice in choices:
            if find(choice, "WriteInData"):
                choice_name = "WRITE-IN"
            else:
                choice_name = find(choice, "Name").text
            vote = find(choice, "Value").text

            cvr["Contests"][contest_name][choice_name] = vote
            contest_choices[contest_name].add(choice_name)

    return cvr


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python -m scripts.parse-xml-cvrs <cvr_directory_path> <output_csv_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    cvr_directory_path = sys.argv[1]
    output_csv_path = sys.argv[2]

    contest_choices: dict = defaultdict(set)
    cvrs = []

    for entry in os.scandir(cvr_directory_path):
        if entry.is_dir():
            print(f"Skipping directory: {entry.name}")
            continue

        try:
            cvr = parse_cvr_file(entry.path)
            cvrs.append(cvr)
        except Exception as exc:
            print(f"Error parsing file: {entry.path}")
            raise exc

        if len(cvrs) % 1000 == 0:
            print(f"Parsed {len(cvrs)} files")

    print("Writing CSV...")

    # Flatten contest choice votes into field names
    # Fill in missing contest choices with 0s
    flat_cvrs = []
    for cvr in cvrs:
        flat_cvr = {
            "CvrGuid": cvr["CvrGuid"],
            "BatchNumber": cvr["BatchNumber"],
            "BatchSequence": cvr["BatchSequence"],
            "SheetNumber": cvr["SheetNumber"],
            "PrecinctSplit": cvr["PrecinctSplit"],
        }

        for contest_name, choices in contest_choices.items():
            for choice_name in choices:
                if contest_name not in cvr["Contests"]:
                    vote = None
                elif choice_name not in cvr["Contests"][contest_name]:
                    vote = 0
                else:
                    vote = cvr["Contests"][contest_name][choice_name]
                flat_cvr[f"{contest_name};{choice_name}"] = vote

        flat_cvrs.append(flat_cvr)

    with open(output_csv_path, "w") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(flat_cvrs[0].keys()))
        writer.writeheader()
        writer.writerows(flat_cvrs)
