import io
import json
import uuid
from collections.abc import Iterable
from typing import TypedDict
import pytest
from flask.testing import FlaskClient

from ...api.contests import JSONDict
from ...api.shared import batch_tallies as contest_batch_tallies
from ...audit_math import macro, sampler, sampler_contest
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import

JURISDICTION_NAMES = ["J1", "J2", "J3"]
CARDS_PER_BATCH = 50
STATEWIDE_CONTESTS = [
    "Governor",
    "Lieutenant Governor",
    "Secretary of State",
    "Attorney General",
]
CANDIDATE_NAMES = ["Candidate A", "Candidate B"]
Candidate = tuple[str, str]  # (contest name, candidate name)


class BatchData(TypedDict):
    cards_by_contest: dict[str, int]
    votes: dict[Candidate, int]


# J1 is a county with several districts, where some batches mix cards from
# different districts and some have no cards at all for a district. J2 and J3
# are single-district counties, so all of their cards carry their contests.
def district_cards(jurisdiction_name: str, batch_index: int) -> dict[str, int]:
    if jurisdiction_name == "J1":
        return {
            "US House District 7": (
                CARDS_PER_BATCH if batch_index <= 20 else 10 if batch_index <= 30 else 0
            ),
            "US House District 13": (
                0 if batch_index <= 20 else 40 if batch_index <= 30 else CARDS_PER_BATCH
            ),
            "State Senate District 5": CARDS_PER_BATCH if batch_index <= 10 else 0,
        }
    if jurisdiction_name == "J2":
        return {
            "US House District 13": CARDS_PER_BATCH,
            "State House District 50": CARDS_PER_BATCH,
        }
    return {
        "US House District 7": CARDS_PER_BATCH,
        "State House District 50": CARDS_PER_BATCH,
    }


def build_batches() -> dict[str, dict[str, BatchData]]:
    batches: dict[str, dict[str, BatchData]] = {}
    for jurisdiction_name, num_batches in [("J1", 40), ("J2", 20), ("J3", 20)]:
        batches[jurisdiction_name] = {}
        for i in range(1, num_batches + 1):
            cards = {contest: CARDS_PER_BATCH for contest in STATEWIDE_CONTESTS}
            cards.update(district_cards(jurisdiction_name, i))
            votes: dict[Candidate, int] = {}
            for k, (contest, num_cards) in enumerate(cards.items()):
                # Vary the results by batch and contest so batches have
                # different selection probabilities, leaving one undervote
                candidate_a = min(int(num_cards * 0.55) + (i + k) % 4, num_cards)
                votes[(contest, "Candidate A")] = candidate_a
                votes[(contest, "Candidate B")] = max(num_cards - candidate_a - 1, 0)
            batches[jurisdiction_name][f"Batch {i:02d}"] = BatchData(
                cards_by_contest=cards, votes=votes
            )
    return batches


BATCHES = build_batches()
CONTEST_NAMES = STATEWIDE_CONTESTS + [
    "US House District 7",
    "US House District 13",
    "State Senate District 5",
    "State House District 50",
]


def contest_jurisdiction_names(contest_name: str) -> list[str]:
    return [
        jurisdiction_name
        for jurisdiction_name, batches in BATCHES.items()
        if any(contest_name in batch["cards_by_contest"] for batch in batches.values())
    ]


def all_batches() -> Iterable[BatchData]:
    return (batch for batches in BATCHES.values() for batch in batches.values())


def total_votes(candidate: Candidate) -> int:
    return sum(batch["votes"].get(candidate, 0) for batch in all_batches())


def total_cards(contest_name: str) -> int:
    return sum(
        batch["cards_by_contest"].get(contest_name, 0) for batch in all_batches()
    )


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return create_election(
        client,
        audit_name=f"Test Audit {request.node.name}",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.CARD_STYLE_DATA,
        organization_id=org_id,
    )


@pytest.fixture
def contest_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
) -> dict[str, str]:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    jurisdiction_id_by_name = dict(zip(JURISDICTION_NAMES, jurisdiction_ids))
    contests: dict[str, JSONDict] = {
        name: {
            "id": str(uuid.uuid4()),
            "name": name,
            "isTargeted": True,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": candidate_name,
                    "numVotes": total_votes((name, candidate_name)),
                }
                for candidate_name in CANDIDATE_NAMES
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": [
                jurisdiction_id_by_name[jurisdiction_name]
                for jurisdiction_name in contest_jurisdiction_names(name)
            ],
            "nestedUnderContestId": None,
        }
        for name in CONTEST_NAMES
    }
    contests["US House District 7"]["nestedUnderContestId"] = contests["Governor"]["id"]
    rv = put_json(
        client, f"/api/election/{election_id}/contest", list(contests.values())
    )
    assert_ok(rv)
    return {name: contest["id"] for name, contest in contests.items()}


def assert_processed(
    client: FlaskClient, election_id: str, jurisdiction_id: str, file: str
):
    processing = get_file_processing(client, election_id, jurisdiction_id, file)
    assert processing["status"] == ProcessingStatus.PROCESSED, processing["error"]


# Manifests with per-contest columns can only be uploaded once contests exist
@pytest.fixture
def manifests(  # pylint: disable=unused-argument
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: dict[str, str],
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        batches = BATCHES[jurisdiction_name]
        # Only contests that aren't on every card need a column
        column_contests = [
            contest
            for contest in next(iter(batches.values()))["cards_by_contest"]
            if any(
                batch["cards_by_contest"][contest] < CARDS_PER_BATCH
                for batch in batches.values()
            )
        ]
        rows = [
            ",".join(
                ["Batch Name", "Number of Ballots"]
                + [f"{contest} - Number of Ballots" for contest in column_contests]
            )
        ] + [
            ",".join(
                [batch_name, str(CARDS_PER_BATCH)]
                + [
                    str(batch["cards_by_contest"][contest])
                    for contest in column_contests
                ]
            )
            for batch_name, batch in batches.items()
        ]
        rv = upload_ballot_manifest(
            client, io.BytesIO("\n".join(rows).encode()), election_id, jurisdiction_id
        )
        assert_ok(rv)
        assert_processed(client, election_id, jurisdiction_id, "ballot-manifest")


@pytest.fixture
def batch_tallies(  # pylint: disable=unused-argument
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    manifests,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        batches = BATCHES[jurisdiction_name]
        candidates = list(next(iter(batches.values()))["votes"])
        rows = [
            ",".join(
                ["Batch Name"]
                + [f"{contest} - {candidate}" for contest, candidate in candidates]
            )
        ] + [
            ",".join(
                [batch_name]
                + [str(batch["votes"][candidate]) for candidate in candidates]
            )
            for batch_name, batch in batches.items()
        ]
        rv = upload_batch_tallies(
            client, io.BytesIO("\n".join(rows).encode()), election_id, jurisdiction_id
        )
        assert_ok(rv)
        assert_processed(client, election_id, jurisdiction_id, "batch-tallies")


def assert_draws_only_where_contest_has_cards(
    draws: dict[str, list[tuple[str, str, str]]],
):
    for contest_name, contest_draws in draws.items():
        for jurisdiction_name, batch_name, _ in contest_draws:
            assert (
                BATCHES[jurisdiction_name][batch_name]["cards_by_contest"].get(
                    contest_name, 0
                )
                > 0
            ), (
                f"{contest_name} drew {jurisdiction_name} {batch_name}, which has no cards for it"
            )


# The sample size the contest would have had with every batch's full card
# count, i.e. without card style data
def diluted_sample_size(contest: Contest) -> int:
    diluted_tallies = {
        batch_key: {contest.id: {**tallies[contest.id], "ballots": CARDS_PER_BATCH}}
        for batch_key, tallies in contest_batch_tallies(contest).items()
    }
    return macro.get_sample_sizes(
        contest.election.risk_limit,
        sampler_contest.from_db_contest(contest),
        diluted_tallies,
        {},
        {},
        [],
    )


@pytest.mark.usefixtures("election_settings", "manifests", "batch_tallies")
def test_card_style_data_end_to_end(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: dict[str, str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Contest totals only count the cards carrying each contest
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    assert {contest["name"]: contest["totalBallotsCast"] for contest in contests} == {
        name: total_cards(name) for name in CONTEST_NAMES
    }

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_sizes = {
        contest_id: sample_size_options[contest_id][0]
        for contest_id in contest_ids.values()
    }
    snapshot.assert_match(
        {
            name: sample_sizes[contest_id]["size"]
            for name, contest_id in contest_ids.items()
        }
    )
    # District contests would need larger samples if every card in their
    # batches counted toward their error bounds
    for name in [
        "US House District 7",
        "US House District 13",
        "State Senate District 5",
    ]:
        contest = Contest.query.get(contest_ids[name])
        assert sample_sizes[contest.id]["size"] < diluted_sample_size(contest)

    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": sample_sizes},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    sample_preview = json.loads(rv.data)["jurisdictions"]

    #
    # Round 1
    #

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": sample_sizes},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    round_1_draws = sampled_batch_draws(round_1_id)
    snapshot.assert_match(round_1_draws)
    for name, contest_id in contest_ids.items():
        assert len(round_1_draws[name]) == sample_sizes[contest_id]["size"]
    assert_draws_only_where_contest_has_cards(round_1_draws)

    # The nested district still stays within its own cards while reusing more
    # of the parent's batches than an independent draw would have
    parent_batches = {(j, b) for j, b, _ in round_1_draws["Governor"]}
    child_batches = {(j, b) for j, b, _ in round_1_draws["US House District 7"]}
    child_contest = Contest.query.get(contest_ids["US House District 7"])
    independent_child_batches = {
        batch_key
        for _, batch_key in sampler.draw_ppeb_sample(
            str(child_contest.election.random_seed),
            sampler_contest.from_db_contest(child_contest),
            sample_sizes[child_contest.id]["size"],
            [],
            contest_batch_tallies(child_contest),
        )
    }
    assert child_batches != independent_child_batches
    assert len(child_batches & parent_batches) > len(
        independent_child_batches & parent_batches
    )

    all_draws = [draw for draws in round_1_draws.values() for draw in draws]
    for jurisdiction_preview in sample_preview:
        jurisdiction_draws = [
            (b, t) for j, b, t in all_draws if j == jurisdiction_preview["name"]
        ]
        assert jurisdiction_preview["numSamples"] == len(jurisdiction_draws)
        assert jurisdiction_preview["numUnique"] == len(
            {b for b, _ in jurisdiction_draws}
        )

    #
    # Enter results exactly as reported, except one US House District 7 batch
    # with its candidates swapped, so that contest alone needs a second round
    #

    choice_id_by_candidate: dict[Candidate, str] = {
        (contest["name"], choice["name"]): choice["id"]
        for contest in contests
        for choice in contest["choices"]
    }
    swapped_jurisdiction_name, swapped_batch_name, _ = round_1_draws[
        "US House District 7"
    ][0]
    swapped_votes = dict(
        BATCHES[swapped_jurisdiction_name][swapped_batch_name]["votes"]
    )
    candidate_a, candidate_b = (
        ("US House District 7", "Candidate A"),
        ("US House District 7", "Candidate B"),
    )
    swapped_votes[candidate_a], swapped_votes[candidate_b] = (
        swapped_votes[candidate_b],
        swapped_votes[candidate_a],
    )
    votes_by_batch_name_by_jurisdiction = {
        jurisdiction_name: {
            batch_name: batch["votes"] for batch_name, batch in batches.items()
        }
        for jurisdiction_name, batches in BATCHES.items()
    }
    votes_by_batch_name_by_jurisdiction[swapped_jurisdiction_name][
        swapped_batch_name
    ] = swapped_votes
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        enter_reported_results(
            client,
            election_id,
            round_1_id,
            jurisdiction_id,
            jurisdiction_name,
            choice_id_by_candidate,
            votes_by_batch_name_by_jurisdiction[jurisdiction_name],
        )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    round_1_contests = {
        round_contest.contest_id: round_contest.is_complete
        for round_contest in RoundContest.query.filter_by(round_id=round_1_id)
    }
    assert round_1_contests == {
        contest_id: name != "US House District 7"
        for name, contest_id in contest_ids.items()
    }

    #
    # Round 2: only the nested district continues, with its draws still
    # derived from Governor's
    #

    district_7_id = contest_ids["US House District 7"]
    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    round_2_sample_sizes = json.loads(rv.data)["sampleSizes"]
    assert list(round_2_sample_sizes) == [district_7_id]
    round_2_sample_size = round_2_sample_sizes[district_7_id][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 2, "sampleSizes": {district_7_id: round_2_sample_size}},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]
    round_2_draws = sampled_batch_draws(round_2_id)
    snapshot.assert_match(round_2_draws)
    assert {name: len(draws) for name, draws in round_2_draws.items()} == {
        "US House District 7": round_2_sample_size["size"]
    }
    assert_draws_only_where_contest_has_cards(round_2_draws)

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
