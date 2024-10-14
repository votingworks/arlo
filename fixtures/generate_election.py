from collections import Counter
import csv
import itertools
import json
import os
import random
import sys
from typing import (
    IO,
    Iterable,
    Literal,
    Tuple,
    TypedDict,
    Dict,
    List,
    Union,
)

SEED = 12345

## Types for the JSON election spec that is provided as input

# { choice_name: votes }
ContestTally = Dict[str, int]


class ContestSpec(TypedDict):
    name: str
    votes_allowed: int
    number_of_winners: int
    tally: ContestTally
    total_ballots_cast: int
    jurisdictions: List[str]


class JurisdictionSpec(TypedDict):
    name: str


class ElectionSpec(TypedDict):
    name: str
    contests: List[ContestSpec]
    jurisdictions: List[JurisdictionSpec]


## Internal types for generation


# Each jurisdiction is only responsible for a portion of the votes
class JurisdictionTally(TypedDict):
    tally: ContestTally
    invalid_votes: int


# { contest_name: JurisdictionTally }
JurisdictionTallies = Dict[str, JurisdictionTally]


class Batch(TypedDict):
    name: str
    tabulator: str


Vote = Union[Literal[1], Literal[0]]
# { choice: Vote }
ContestVotes = Dict[str, Vote]
# { contest_name: ContestVotes }
BallotVotes = Dict[str, ContestVotes]


class Ballot(TypedDict):
    batch: Batch
    ballot_number: int
    votes: BallotVotes


Cvrs = Iterable[Ballot]

# (batch, num_ballots)
Manifest = Iterable[Tuple[Batch, int]]

# (batch_name, ContestTally)
BatchTallies = Iterable[Tuple[str, ContestTally]]


def generate_contest_votes(
    jurisdiction_tally: JurisdictionTally,
) -> Iterable[ContestVotes]:
    choice_names = jurisdiction_tally["tally"].keys()
    for voted_choice_name, votes in jurisdiction_tally["tally"].items():
        for _ in range(votes):
            yield {
                choice_name: 1 if choice_name == voted_choice_name else 0
                for choice_name in choice_names
            }  # type: ignore

    overvotes = round(jurisdiction_tally["invalid_votes"] / 2)
    undervotes = jurisdiction_tally["invalid_votes"] - overvotes
    for _ in range(overvotes):
        yield {choice_name: 1 for choice_name in choice_names}  # type: ignore
    for _ in range(undervotes):
        yield {choice_name: 0 for choice_name in choice_names}  # type: ignore


def safe_dict(*args):
    return dict(filter(lambda x: x is not None, *args))


def generate_ballot_votes(tallies: JurisdictionTallies) -> Iterable[BallotVotes]:
    contest_votes = {
        contest_name: list(generate_contest_votes(tally))
        for contest_name, tally in tallies.items()
    }
    num_ballots = max((len(votes) for votes in contest_votes.values()), default=0)
    for i in range(num_ballots):
        yield {
            contest_name: votes[i]
            for contest_name, votes in contest_votes.items()
            if i < len(votes)
        }


# In batch comparison audits, batch names must be unique within a jurisdiction,
# so we'll stick to that constraint. However, we'll still add in a tabulator for
# color.
def generate_batches(
    min_size: int, max_size: int, rand: random.Random
) -> Iterable[Tuple[Batch, int]]:
    for batch_number in itertools.count(1):
        tabulator = "ABC"[(batch_number - 1) % 3]
        yield (
            Batch(
                name=f"Batch {batch_number}",
                tabulator=f"Tabulator {tabulator}",
            ),
            rand.randint(min_size, max_size),
        )


def generate_cvrs(
    jurisdiction_tallies: JurisdictionTallies,
    contests: List[ContestSpec],
    rand: random.Random,
) -> Cvrs:
    min_batch_size = contests[0]["total_ballots_cast"] // 100
    max_batch_size = contests[0]["total_ballots_cast"] // 10
    batches = generate_batches(min_batch_size, max_batch_size, rand)
    contest_votes = list(generate_ballot_votes(jurisdiction_tallies))
    rand.shuffle(contest_votes)
    batch_ballot_numbers = itertools.chain.from_iterable(
        ((batch, i + 1) for i in range(batch_size)) for batch, batch_size in batches
    )
    for (batch, ballot_number), votes in zip(batch_ballot_numbers, contest_votes):
        yield Ballot(
            batch=batch,
            ballot_number=ballot_number,
            votes=votes,
        )


def write_dominion_cvrs(election_spec: ElectionSpec, cvrs: Cvrs, output_file: IO):
    metadata_columns = [
        "CvrNumber",
        "TabulatorNum",
        "BatchId",
        "RecordId",
        "ImprintedId",
        "CountingGroup",
        "PrecinctPortion",
        "BallotType",
    ]
    contest_columns = [
        (contest, choice_name)
        for contest in election_spec["contests"]
        for choice_name in contest["tally"]
    ]

    writer = csv.writer(output_file)
    writer.writerow(
        [election_spec["name"], "5.2.16.1"]
        + ["" for _ in metadata_columns[2:]]
        + ["" for _ in contest_columns]
    )
    writer.writerow(
        ["" for _ in metadata_columns]
        + [
            f"{contest['name']} (Vote For={contest['votes_allowed']})"
            for contest, _ in contest_columns
        ]
    )
    writer.writerow(
        ["" for _ in metadata_columns]
        + [choice_name for _, choice_name in contest_columns]
    )
    writer.writerow(metadata_columns + ["" for _ in contest_columns])

    for cvr_number, ballot in enumerate(cvrs):
        batch = ballot["batch"]
        writer.writerow(
            [
                cvr_number,  # CvrNumber
                batch["tabulator"],  # TabulatorNum
                batch["name"],  # BatchId
                ballot["ballot_number"],  # RecordId
                f"{batch['tabulator']}-{batch['name']}-{ballot['ballot_number']}",  # ImprintedId
                # TODO better CountingGroups
                "Election Day",  # CountingGroup
                "precinct-portion-1",  # PrecinctPortion
                "ballot-type-1",  # BallotType
            ]
            + [
                (
                    ballot["votes"][contest["name"]][choice_name]
                    if contest["name"] in ballot["votes"]
                    else ""
                )
                for contest, choice_name in contest_columns
            ]
        )


def cvrs_to_manifest(cvrs: Cvrs) -> Manifest:
    counter: Dict[Tuple[str, str], int] = Counter()
    for ballot in cvrs:
        batch = ballot["batch"]
        # Can't hash a dict, so convert Batch to a tuple
        counter[(batch["tabulator"], batch["name"])] += 1
    return [
        (Batch(tabulator=tabulator, name=name), num_ballots)
        for (tabulator, name), num_ballots in counter.items()
    ]


def write_manifest(manifest: Manifest, output_file: IO):
    writer = csv.writer(output_file)
    writer.writerow(["Tabulator", "Batch Name", "Number of Ballots"])
    for batch, num_ballots in manifest:
        writer.writerow([batch["tabulator"], batch["name"], num_ballots])


def cvrs_to_batch_tallies(cvrs: Cvrs, contest: ContestSpec) -> BatchTallies:
    batch_tallies = {}
    for ballot in cvrs:
        batch_name = ballot["batch"]["name"]
        if batch_name not in batch_tallies:
            batch_tallies[batch_name] = Counter(
                {choice_name: 0 for choice_name in contest["tally"]}
            )

        # Skip contests not on ballot
        if contest["name"] not in ballot["votes"]:
            continue

        # Skip overvotes
        if sum(ballot["votes"][contest["name"]].values()) > contest["votes_allowed"]:
            continue

        batch_tallies[batch_name].update(ballot["votes"][contest["name"]])

    return [
        (batch_name, dict(counter)) for batch_name, counter in batch_tallies.items()
    ]


def write_batch_tallies(
    batch_tallies: BatchTallies, contest: ContestSpec, output_file: IO
):
    choice_names = list(contest["tally"].keys())
    writer = csv.writer(output_file)
    writer.writerow(["Batch Name"] + choice_names)
    for batch_name, tally in batch_tallies:
        writer.writerow(
            [batch_name] + [str(tally[choice_name]) for choice_name in choice_names]
        )


def random_numbers_that_sum_to_total(
    total: int, num_numbers: int, rand: random.Random
) -> List[int]:
    if num_numbers == 0:
        raise ValueError("num_numbers must be > 0")
    numbers = []
    total_left = total
    for _ in range(num_numbers - 1):
        number = rand.randint(0, total_left)
        numbers.append(number)
        total_left -= number
    numbers.append(total_left)
    rand.shuffle(numbers)
    return numbers


def split_contest_tallies_across_jurisdictions(
    election_spec: ElectionSpec,
    rand: random.Random,
) -> Dict[str, JurisdictionTallies]:
    jurisdiction_tallies: Dict[str, JurisdictionTallies] = {
        jurisdiction["name"]: {} for jurisdiction in election_spec["jurisdictions"]
    }
    for contest in election_spec["contests"]:
        contest_jurisdictions = contest["jurisdictions"]
        total_votes = sum(contest["tally"].values())
        invalid_votes = contest["total_ballots_cast"] - total_votes
        jurisdiction_invalid_votes = random_numbers_that_sum_to_total(
            invalid_votes, len(contest_jurisdictions), rand
        )
        for jurisdiction, invalid_votes in zip(
            contest_jurisdictions, jurisdiction_invalid_votes
        ):
            jurisdiction_tallies[jurisdiction][contest["name"]] = JurisdictionTally(
                tally={}, invalid_votes=invalid_votes
            )
        for choice_name, choice_votes in contest["tally"].items():
            jurisdiction_choice_votes = random_numbers_that_sum_to_total(
                choice_votes, len(contest_jurisdictions), rand
            )
            for jurisdiction_name, votes in zip(
                contest_jurisdictions, jurisdiction_choice_votes
            ):
                jurisdiction_tallies[jurisdiction_name][contest["name"]]["tally"][
                    choice_name
                ] = votes
    return jurisdiction_tallies


def generate_jurisdiction_admins(
    jurisdictions: List[JurisdictionSpec],
) -> Dict[str, List[str]]:
    return {
        jurisdiction["name"]: [
            f"admin-{jurisdiction['name'].replace(' ', '-')}@example.com"
        ]
        for jurisdiction in jurisdictions
    }


def write_jurisdictions(jurisdiction_admins: Dict[str, List[str]], output_file: IO):
    writer = csv.writer(output_file)
    writer.writerow(["Jurisdiction", "Admin Email"])
    for jurisdiction_name, admins in jurisdiction_admins.items():
        for admin in admins:
            writer.writerow([jurisdiction_name, admin])


def write_standardized_contests(election_spec: ElectionSpec, output_file: IO):
    writer = csv.writer(output_file)
    writer.writerow(["Contest Name", "Jurisdictions"])
    for contest in election_spec["contests"]:
        contest_jurisdictions = (
            "all"
            if len(contest["jurisdictions"]) == len(election_spec["jurisdictions"])
            else ", ".join(contest["jurisdictions"])
        )
        writer.writerow([contest["name"], contest_jurisdictions])


def generate_election(election_spec: ElectionSpec, output_dir_path: str):
    rand = random.Random(SEED)

    jurisdiction_admins = generate_jurisdiction_admins(election_spec["jurisdictions"])
    with open(
        os.path.join(output_dir_path, f"{election_spec['name']} - jurisdictions.csv"),
        "w",
        encoding="utf8",
    ) as jurisdictions_file:
        write_jurisdictions(jurisdiction_admins, jurisdictions_file)

    with open(
        os.path.join(
            output_dir_path, f"{election_spec['name']} - standardized contests.csv"
        ),
        "w",
        encoding="utf8",
    ) as standardized_contests_file:
        write_standardized_contests(election_spec, standardized_contests_file)

    jurisdiction_tallies = split_contest_tallies_across_jurisdictions(
        election_spec, rand
    )

    for jurisdiction_name, jurisdiction_tally in jurisdiction_tallies.items():
        cvrs = list(generate_cvrs(jurisdiction_tally, election_spec["contests"], rand))
        with open(
            os.path.join(output_dir_path, f"{jurisdiction_name} - cvrs.csv"),
            "w",
            encoding="utf8",
        ) as cvrs_file:
            write_dominion_cvrs(election_spec, cvrs, cvrs_file)

        manifest = cvrs_to_manifest(cvrs)
        with open(
            os.path.join(output_dir_path, f"{jurisdiction_name} - ballot manifest.csv"),
            "w",
            encoding="utf8",
        ) as manifest_file:
            write_manifest(manifest, manifest_file)

        for contest in election_spec["contests"]:
            if contest["name"] in jurisdiction_tally:
                batch_tallies = cvrs_to_batch_tallies(cvrs, contest)
                with open(
                    os.path.join(
                        output_dir_path,
                        f"{jurisdiction_name} - {contest['name']} - candidate totals by batch.csv",
                    ),
                    "w",
                    encoding="utf8",
                ) as batch_tallies_file:
                    write_batch_tallies(batch_tallies, contest, batch_tallies_file)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python -m fixtures.generate-election <path-to-election-spec.json> <path-to-output-dir>"
        )
        sys.exit(1)

    election_spec_path = sys.argv[1]
    with open(election_spec_path, encoding="utf8") as election_spec_file:
        election_spec = json.loads(election_spec_file.read())

    # TODO validate election spec

    output_dir_path = sys.argv[2]

    # Delete previously generated files in output directory
    for item in os.listdir(output_dir_path):
        if item.endswith(".csv"):
            os.remove(os.path.join(output_dir_path, item))

    generate_election(election_spec, output_dir_path)
