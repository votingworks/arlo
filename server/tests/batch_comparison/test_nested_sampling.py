import json
import uuid
import pytest
from flask.testing import FlaskClient

from ...api.contests import JSONDict
from ...api.shared import batch_tallies as contest_batch_tallies
from ...audit_math import sampler, sampler_contest
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .test_multi_contest_batch_comparison import put_batch_results

JURISDICTION_NAMES = ["J1", "J2", "J3"]
BALLOTS_PER_BATCH = 50
Candidate = tuple[str, str]  # (contest name, candidate name)


# Contest 1 is in every jurisdiction and Contest 2 only in J1, which has enough
# batches that Contest 2 can keep sampling in round 2 without a full hand tally.
# Contest 1's results vary by batch so that batches have different selection
# probabilities, while Contest 2's are the same in every batch.
def build_batch_votes() -> dict[str, dict[str, dict[Candidate, int]]]:
    votes: dict[str, dict[str, dict[Candidate, int]]] = {
        name: {} for name in JURISDICTION_NAMES
    }
    for i in range(1, 41):
        candidate_1 = 30 + 5 * (i % 3)
        votes["J1"][f"Batch {i:02d}"] = {
            ("Contest 1", "Candidate 1"): candidate_1,
            ("Contest 1", "Candidate 2"): BALLOTS_PER_BATCH - candidate_1,
            ("Contest 2", "Candidate 3"): 40,
            ("Contest 2", "Candidate 4"): 10,
        }
    for jurisdiction_name in ["J2", "J3"]:
        for i in range(1, 5):
            votes[jurisdiction_name][f"Batch {i}"] = {
                ("Contest 1", "Candidate 1"): 35,
                ("Contest 1", "Candidate 2"): 15,
            }
    return votes


BATCH_VOTES = build_batch_votes()


def total_votes(candidate: Candidate) -> int:
    return sum(
        batch_votes.get(candidate, 0)
        for batches in BATCH_VOTES.values()
        for batch_votes in batches.values()
    )


def contest_json(
    name: str,
    candidate_names: list[str],
    jurisdiction_ids: list[str],
    nested_under_contest_id: str | None = None,
) -> JSONDict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "isTargeted": True,
        "choices": [
            {
                "id": str(uuid.uuid4()),
                "name": candidate_name,
                "numVotes": total_votes((name, candidate_name)),
            }
            for candidate_name in candidate_names
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
        "nestedUnderContestId": nested_under_contest_id,
    }


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    parent = contest_json("Contest 1", ["Candidate 1", "Candidate 2"], jurisdiction_ids)
    child = contest_json(
        "Contest 2",
        ["Candidate 3", "Candidate 4"],
        jurisdiction_ids[:1],
        nested_under_contest_id=parent["id"],
    )
    rv = put_json(client, f"/api/election/{election_id}/contest", [parent, child])
    assert_ok(rv)
    return [parent["id"], child["id"]]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        rows = ["Batch Name,Number of Ballots"] + [
            f"{batch_name},{BALLOTS_PER_BATCH}"
            for batch_name in BATCH_VOTES[jurisdiction_name]
        ]
        rv = upload_ballot_manifest(
            client, io.BytesIO("\n".join(rows).encode()), election_id, jurisdiction_id
        )
        assert_ok(rv)


@pytest.fixture
def batch_tallies(  # pylint: disable=unused-argument
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    manifests,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        batches = BATCH_VOTES[jurisdiction_name]
        candidates = list(next(iter(batches.values())))
        rows = [
            ",".join(
                ["Batch Name"]
                + [f"{contest} - {candidate}" for contest, candidate in candidates]
            )
        ] + [
            ",".join([batch_name] + [str(votes[candidate]) for candidate in candidates])
            for batch_name, votes in batches.items()
        ]
        rv = upload_batch_tallies(
            client, io.BytesIO("\n".join(rows).encode()), election_id, jurisdiction_id
        )
        assert_ok(rv)


# { contest name: [(jurisdiction name, batch name, ticket number)] }
def sampled_batch_draws(round_id: str) -> dict[str, list[tuple[str, str, str]]]:
    draws = (
        SampledBatchDraw.query.filter_by(round_id=round_id)
        .join(Batch)
        .join(Jurisdiction)
        .join(Contest, SampledBatchDraw.contest_id == Contest.id)
        .with_entities(
            Contest.name, Jurisdiction.name, Batch.name, SampledBatchDraw.ticket_number
        )
        .all()
    )
    draws_by_contest: dict[str, list[tuple[str, str, str]]] = {}
    for contest_name, jurisdiction_name, batch_name, ticket_number in draws:
        draws_by_contest.setdefault(contest_name, []).append(
            (jurisdiction_name, batch_name, ticket_number)
        )
    return {name: sorted(rows) for name, rows in draws_by_contest.items()}


def enter_reported_results(
    client: FlaskClient,
    election_id: str,
    round_id: str,
    jurisdiction_id: str,
    jurisdiction_name: str,
    choice_id_by_candidate: dict[Candidate, str],
    overrides: dict[str, dict[Candidate, int]],
):
    # J1 and J2 share an admin in the jurisdictions file; J3 has its own
    set_logged_in_user(
        client,
        UserType.JURISDICTION_ADMIN,
        f"j3-{election_id}@example.com"
        if jurisdiction_name == "J3"
        else default_ja_email(election_id),
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches"
    )
    for batch in json.loads(rv.data)["batches"]:
        votes = overrides.get(
            batch["name"], BATCH_VOTES[jurisdiction_name][batch["name"]]
        )
        results = {
            choice_id_by_candidate[candidate]: count
            for candidate, count in votes.items()
        }
        rv = put_batch_results(
            client, election_id, jurisdiction_id, round_id, batch["id"], [results]
        )
        assert_ok(rv)
    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches/finalize"
    )
    assert_ok(rv)


@pytest.mark.usefixtures("election_settings", "manifests", "batch_tallies")
def test_nested_sampling_end_to_end(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    parent_id, child_id = contest_ids

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_sizes = {
        contest_id: sample_size_options[contest_id][0] for contest_id in contest_ids
    }
    snapshot.assert_match(
        {
            "Contest 1": sample_sizes[parent_id]["size"],
            "Contest 2": sample_sizes[child_id]["size"],
        }
    )

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
    assert len(round_1_draws["Contest 1"]) == sample_sizes[parent_id]["size"]
    assert len(round_1_draws["Contest 2"]) == sample_sizes[child_id]["size"]
    parent_batches = {(j, b) for j, b, _ in round_1_draws["Contest 1"]}
    child_batches = {(j, b) for j, b, _ in round_1_draws["Contest 2"]}
    # Contest 2 is only on the ballot in J1
    assert all(j == "J1" for j, _ in child_batches)

    # Nesting changed which batches Contest 2 drew, and made them overlap the
    # parent's more than an independent draw would have
    child_contest = Contest.query.get(child_id)
    independent_child_batches = {
        batch_key
        for _, batch_key in sampler.draw_ppeb_sample(
            str(child_contest.election.random_seed),
            sampler_contest.from_db_contest(child_contest),
            sample_sizes[child_id]["size"],
            [],
            contest_batch_tallies(child_contest),
        )
    }
    assert child_batches != independent_child_batches
    assert len(child_batches & parent_batches) > len(
        independent_child_batches & parent_batches
    )

    # The sample preview matches the sample drawn
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
    # Enter results: Contest 1 exactly as reported, so it completes, and one
    # Contest 2 batch with its candidates swapped, so Contest 2 does not
    #

    rv = client.get(f"/api/election/{election_id}/contest")
    choice_id_by_candidate: dict[Candidate, str] = {
        (contest["name"], choice["name"]): choice["id"]
        for contest in json.loads(rv.data)["contests"]
        for choice in contest["choices"]
    }
    swapped_batch_name = sorted(child_batches)[0][1]
    swapped_votes = dict(BATCH_VOTES["J1"][swapped_batch_name])
    (
        swapped_votes[("Contest 2", "Candidate 3")],
        swapped_votes[("Contest 2", "Candidate 4")],
    ) = (
        swapped_votes[("Contest 2", "Candidate 4")],
        swapped_votes[("Contest 2", "Candidate 3")],
    )
    for jurisdiction_id, jurisdiction_name in zip(jurisdiction_ids, JURISDICTION_NAMES):
        enter_reported_results(
            client,
            election_id,
            round_1_id,
            jurisdiction_id,
            jurisdiction_name,
            choice_id_by_candidate,
            overrides={swapped_batch_name: swapped_votes}
            if jurisdiction_name == "J1"
            else {},
        )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    round_1_contests = {
        round_contest.contest_id: round_contest.is_complete
        for round_contest in RoundContest.query.filter_by(round_id=round_1_id)
    }
    assert round_1_contests == {parent_id: True, child_id: False}

    #
    # Round 2: only Contest 2 continues, but its draws are still derived from
    # Contest 1's
    #

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    round_2_sample_sizes = json.loads(rv.data)["sampleSizes"]
    assert list(round_2_sample_sizes) == [child_id]
    round_2_sample_size = round_2_sample_sizes[child_id][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 2, "sampleSizes": {child_id: round_2_sample_size}},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]
    round_2_draws = sampled_batch_draws(round_2_id)
    snapshot.assert_match(round_2_draws)
    assert {name: len(draws) for name, draws in round_2_draws.items()} == {
        "Contest 2": round_2_sample_size["size"]
    }

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
