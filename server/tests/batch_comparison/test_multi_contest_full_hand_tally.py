import pytest
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *
from .test_multi_contest_batch_comparison import put_batch_results

NUM_BATCHES = [20, 20, 10]


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    def contest(name: str, choice_names: list[str], num_batches: int, jurisdictions):
        return {
            "id": str(uuid.uuid4()),
            "name": name,
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": choice_name, "numVotes": votes}
                for choice_name, votes in zip(
                    choice_names, [70 * num_batches, 30 * num_batches]
                )
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdictions,
        }

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        contest("Contest 1", ["A", "B"], sum(NUM_BATCHES), jurisdiction_ids),
        contest("Contest 2", ["C", "D"], sum(NUM_BATCHES[:2]), jurisdiction_ids[:2]),
        contest("Contest 3", ["E", "F"], NUM_BATCHES[2], jurisdiction_ids[2:]),
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = put_json(
        client,
        f"/api/election/{election_id}/settings",
        {
            "electionName": "Test Election",
            "online": False,
            # Samples a Contest 3 batch for only Contest 1 in round 1
            "randomSeed": "7",
            "riskLimit": 10,
            "state": USState.California,
        },
    )
    assert_ok(rv)


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for jurisdiction_id, num_batches in zip(jurisdiction_ids, NUM_BATCHES):
        manifest = "Batch Name,Number of Ballots\n" + "".join(
            f"Batch {i},100\n" for i in range(1, num_batches + 1)
        )
        rv = upload_ballot_manifest(
            client, io.BytesIO(manifest.encode()), election_id, jurisdiction_id
        )
        assert_ok(rv)


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids,
    manifests,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    for i, (jurisdiction_id, num_batches) in enumerate(
        zip(jurisdiction_ids, NUM_BATCHES)
    ):
        local_contest = (
            "Contest 2 - C,Contest 2 - D" if i < 2 else "Contest 3 - E,Contest 3 - F"
        )
        batch_tallies_csv = (
            f"Batch Name,Contest 1 - A,Contest 1 - B,{local_contest}\n"
            + "".join(f"Batch {j},70,30,70,30\n" for j in range(1, num_batches + 1))
        )
        rv = upload_batch_tallies(
            client,
            io.BytesIO(batch_tallies_csv.encode()),
            election_id,
            jurisdiction_id,
        )
        assert_ok(rv)


def ja_email(election_id: str, jurisdiction_index: int) -> str:
    return (
        f"j3-{election_id}@example.com"
        if jurisdiction_index == 2
        else default_ja_email(election_id)
    )


def start_round(client: FlaskClient, election_id: str, round_num: int, sample_sizes):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": round_num, "sampleSizes": sample_sizes},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    return json.loads(rv.data)["rounds"][round_num - 1]


def default_sample_sizes(client: FlaskClient, election_id: str, round_num: int):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/{round_num}")
    return {
        contest_id: options[0]
        for contest_id, options in json.loads(rv.data)["sampleSizes"].items()
    }


# Records results for every batch sampled in the round, shifting the given number
# of votes per batch from each contest's winner to its loser. Returns the contest
# names entered for each batch, by jurisdiction.
def audit_round(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_id: str,
    overstatements: dict[str, int],
) -> list[dict[str, set[str]]]:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    contest_names = {contest["id"]: contest["name"] for contest in contests}
    results_by_contest_id = {}
    for contest in contests:
        overstatement = overstatements.get(contest["name"], 0)
        winner, loser = sorted(contest["choices"], key=lambda choice: choice["name"])
        results_by_contest_id[contest["id"]] = {
            winner["id"]: 70 - overstatement,
            loser["id"]: 30 + overstatement,
        }

    sampled_batch_contests: list[dict[str, set[str]]] = []
    for i, jurisdiction_id in enumerate(jurisdiction_ids):
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, ja_email(election_id, i)
        )
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches"
        )
        batches = json.loads(rv.data)["batches"]
        jurisdiction_batch_contests: dict[str, set[str]] = {}
        for batch in batches:
            batch_contest_ids = batch["contestIdsToAudit"]
            jurisdiction_batch_contests[batch["name"]] = {
                contest_names[contest_id] for contest_id in batch_contest_ids
            }
            results = {
                choice_id: votes
                for contest_id in batch_contest_ids
                for choice_id, votes in results_by_contest_id[contest_id].items()
            }
            rv = put_batch_results(
                client, election_id, jurisdiction_id, round_id, batch["id"], [results]
            )
            assert_ok(rv)
        sampled_batch_contests.append(jurisdiction_batch_contests)
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches/finalize",
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    return sampled_batch_contests


def round_contest_status(round_id: str) -> dict[str, tuple[bool, float]]:
    return {
        round_contest.contest.name: (
            round_contest.is_complete,
            round_contest.end_p_value,
        )
        for round_contest in RoundContest.query.filter_by(round_id=round_id)
    }


def contest_3_sampled_batch_names(contest_ids: list[str]) -> set[str]:
    return {
        draw.batch.name
        for draw in SampledBatchDraw.query.filter_by(contest_id=contest_ids[2])
    }


ALL_CONTEST_3_BATCH_NAMES = {f"Batch {i}" for i in range(1, NUM_BATCHES[2] + 1)}


def batches_audited_for(contest_name: str, batch_contests: dict[str, set[str]]):
    return {
        name for name, contests in batch_contests.items() if contest_name in contests
    }


def test_full_hand_tally_of_one_contest_in_first_round(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
):
    sample_sizes = default_sample_sizes(client, election_id, 1)
    sample_sizes[contest_ids[2]] = {
        "key": "custom",
        "size": NUM_BATCHES[2],
        "prob": None,
    }
    round_1 = start_round(client, election_id, 1, sample_sizes)
    assert round_1["needsFullHandTally"] is True
    assert round_1["isFullHandTally"] is False
    assert contest_3_sampled_batch_names(contest_ids) == ALL_CONTEST_3_BATCH_NAMES

    batch_contests = audit_round(
        client, election_id, jurisdiction_ids, round_1["id"], {}
    )
    assert batches_audited_for("Contest 3", batch_contests[2]) == (
        ALL_CONTEST_3_BATCH_NAMES
    )
    assert round_contest_status(round_1["id"])["Contest 3"] == (True, 0)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][0]["isAuditComplete"] is True


def test_full_hand_tally_of_two_contests_in_first_round(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
):
    sample_sizes = default_sample_sizes(client, election_id, 1)
    for contest_id, size in [
        (contest_ids[0], sum(NUM_BATCHES)),
        (contest_ids[1], sum(NUM_BATCHES[:2])),
    ]:
        sample_sizes[contest_id] = {"key": "custom", "size": size, "prob": None}
    round_1 = start_round(client, election_id, 1, sample_sizes)
    assert round_1["needsFullHandTally"] is True
    assert round_1["isFullHandTally"] is False

    batch_contests = audit_round(
        client, election_id, jurisdiction_ids, round_1["id"], {}
    )
    for i, num_batches in enumerate(NUM_BATCHES):
        all_batch_names = {f"Batch {j}" for j in range(1, num_batches + 1)}
        assert batches_audited_for("Contest 1", batch_contests[i]) == all_batch_names
        if i < 2:
            assert (
                batches_audited_for("Contest 2", batch_contests[i]) == all_batch_names
            )
    status = round_contest_status(round_1["id"])
    assert status["Contest 1"] == (True, 0)
    assert status["Contest 2"] == (True, 0)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][0]["isAuditComplete"] is True


def test_full_hand_tally_of_one_contest_after_escalation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
):
    round_1 = start_round(
        client, election_id, 1, default_sample_sizes(client, election_id, 1)
    )
    assert round_1["needsFullHandTally"] is False
    round_1_batch_contests = audit_round(
        client,
        election_id,
        jurisdiction_ids,
        round_1["id"],
        {"Contest 1": 10, "Contest 3": 20},
    )
    status = round_contest_status(round_1["id"])
    assert status["Contest 1"][0] is False
    assert status["Contest 2"][0] is True
    assert status["Contest 3"][0] is False

    sample_sizes = default_sample_sizes(client, election_id, 2)
    assert set(sample_sizes) == {contest_ids[0], contest_ids[2]}
    round_2 = start_round(client, election_id, 2, sample_sizes)
    assert round_2["needsFullHandTally"] is True
    assert round_2["isFullHandTally"] is False
    assert contest_3_sampled_batch_names(contest_ids) == ALL_CONTEST_3_BATCH_NAMES

    round_2_batch_contests = audit_round(
        client, election_id, jurisdiction_ids, round_2["id"], {}
    )
    round_1_contest_3_batches = batches_audited_for(
        "Contest 3", round_1_batch_contests[2]
    )
    assert batches_audited_for("Contest 3", round_2_batch_contests[2]) == (
        ALL_CONTEST_3_BATCH_NAMES - round_1_contest_3_batches
    )
    status = round_contest_status(round_2["id"])
    assert status["Contest 1"][0] is True
    assert status["Contest 3"] == (True, 0)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][1]["isAuditComplete"] is True
