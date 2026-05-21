import io
import json
import uuid
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def _runoff_contest(jurisdiction_ids: list[str], **overrides) -> dict:
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Runoff Contest",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 4000},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 3500},
            {"id": str(uuid.uuid4()), "name": "Carla", "numVotes": 1500},
            {"id": str(uuid.uuid4()), "name": "Dan", "numVotes": 1000},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
        "isSubjectToRunoff": True,
    }
    contest.update(overrides)
    return contest


def test_runoff_flag_serialized_for_batch_comparison(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids)

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    assert len(contests) == 1
    assert contests[0]["isSubjectToRunoff"] is True


def test_runoff_flag_defaults_to_false_when_omitted(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids)
    del contest["isSubjectToRunoff"]

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    assert contests[0]["isSubjectToRunoff"] is False


def test_runoff_flag_rejects_num_winners_not_one(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids, numWinners=2)

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "isSubjectToRunoff can only be true for contests with num_winners=1",
                "errorType": "Bad Request",
            }
        ]
    }


def test_runoff_flag_requires_three_or_more_choices(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(
        jurisdiction_ids,
        choices=[
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 4000},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 3500},
        ],
    )

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "isSubjectToRunoff can only be true for contests with at least 3 choices",
                "errorType": "Bad Request",
            }
        ]
    }


def test_end_to_end_runoff_no_majority_audit(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    # Full audit cycle for a Georgia batch comparison audit with a
    # runoff-subject contest in the no-majority case: Alice 40 / Bob 35 /
    # Carla 15 / Dan 10 per batch, 10 batches, 1000 ballots total. Sample
    # results match reported exactly (no discrepancies) — the audit should
    # clear and the report should surface the runoff outcome.

    # 1. Set state=GA + base audit settings.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = put_json(
        client,
        f"/api/election/{election_id}/settings",
        {
            "electionName": "Test Election",
            "online": False,
            "randomSeed": "1234567890",
            "riskLimit": 10,
            "state": USState.Georgia,
        },
    )
    assert_ok(rv)

    # 2. Configure a runoff-subject contest scoped to J1 only.
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Runoff Contest",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 400},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 350},
            {"id": str(uuid.uuid4()), "name": "Carla", "numVotes": 150},
            {"id": str(uuid.uuid4()), "name": "Dan", "numVotes": 100},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": [jurisdiction_ids[0]],
        "isSubjectToRunoff": True,
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    # 3. Upload manifest + matching batch tallies on J1.
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    manifest_csv = b"Batch Name,Number of Ballots\n" + b"".join(
        f"Batch {i},100\n".encode() for i in range(1, 11)
    )
    rv = upload_ballot_manifest(
        client, io.BytesIO(manifest_csv), election_id, jurisdiction_ids[0]
    )
    assert_ok(rv)

    tallies_csv = b"Batch Name,Alice,Bob,Carla,Dan\n" + b"".join(
        f"Batch {i},40,35,15,10\n".encode() for i in range(1, 11)
    )
    rv = upload_batch_tallies(
        client, io.BytesIO(tallies_csv), election_id, jurisdiction_ids[0]
    )
    assert_ok(rv)

    # 4. Start round 1 with the first suggested sample size.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)
    round_id = json.loads(client.get(f"/api/election/{election_id}/round").data)[
        "rounds"
    ][0]["id"]

    # 5. As JA, fetch sampled batches and submit results matching reported
    #    (zero discrepancies).
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) > 0, "Expected at least one sampled batch"

    choice_ids = [choice["id"] for choice in contest["choices"]]
    for batch in batches:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches/{batch['id']}/results",
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {
                        choice_ids[0]: 40,
                        choice_ids[1]: 35,
                        choice_ids[2]: 15,
                        choice_ids[3]: 10,
                    },
                }
            ],
        )
        assert_ok(rv)

    rv = client.post(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches/finalize"
    )
    assert_ok(rv)

    # 6. End the round; with zero discrepancies the runoff-subject contest
    #    should reach the risk limit and be marked complete.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    round_contest = RoundContest.query.filter_by(round_id=round_id).one()
    assert round_contest.is_complete is True

    # 7. Download the audit report and assert the new runoff columns appear
    #    in the CONTESTS section with the expected outcome.
    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    report_csv = rv.data.decode("utf-8")
    assert "Runoff Law" in report_csv
    assert "Reported Runoff Results" in report_csv
    assert "Subject to runoff law" in report_csv
    assert "No majority, runoff required" in report_csv


def test_end_to_end_runoff_majority_threshold_drives_round_1_failure(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
):
    # Majority case where the threshold pair (V_wl=600) is uniquely tight
    # compared to the pairwise pairs (Alice-Bob V_wl=650, Alice-Carla=770,
    # Alice-Dan=780). Round 1 submits Alice→Bob shift discrepancies on every
    # sampled batch — small in absolute terms but disproportionate against
    # the threshold pair's small margin. Round 1 fails; round 2 samples the
    # remaining batches with clean results and clears.

    # 1. Audit settings.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = put_json(
        client,
        f"/api/election/{election_id}/settings",
        {
            "electionName": "Test Election",
            "online": False,
            "randomSeed": "1234567890",
            "riskLimit": 10,
            "state": USState.Georgia,
        },
    )
    assert_ok(rv)

    # 2. Runoff-subject contest. Alice clears majority globally (80%).
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Runoff Contest",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 800},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 150},
            {"id": str(uuid.uuid4()), "name": "Carla", "numVotes": 30},
            {"id": str(uuid.uuid4()), "name": "Dan", "numVotes": 20},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": [jurisdiction_ids[0]],
        "isSubjectToRunoff": True,
    }
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    # 3. Manifest + matching batch tallies on J1.
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    manifest_csv = b"Batch Name,Number of Ballots\n" + b"".join(
        f"Batch {i},100\n".encode() for i in range(1, 11)
    )
    rv = upload_ballot_manifest(
        client, io.BytesIO(manifest_csv), election_id, jurisdiction_ids[0]
    )
    assert_ok(rv)

    tallies_csv = b"Batch Name,Alice,Bob,Carla,Dan\n" + b"".join(
        f"Batch {i},80,15,3,2\n".encode() for i in range(1, 11)
    )
    rv = upload_batch_tallies(
        client, io.BytesIO(tallies_csv), election_id, jurisdiction_ids[0]
    )
    assert_ok(rv)

    choice_ids = [choice["id"] for choice in contest["choices"]]

    def submit_batch_results(round_id: str, results_by_batch: dict):
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches"
        )
        assert rv.status_code == 200
        batches = json.loads(rv.data)["batches"]
        for batch in batches:
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches/{batch['id']}/results",
                [{"name": "Tally Sheet #1", "results": results_by_batch}],
            )
            assert_ok(rv)
        rv = client.post(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/batches/finalize"
        )
        assert_ok(rv)

    def start_round(round_num: int) -> str:
        set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
        rv = client.get(f"/api/election/{election_id}/sample-sizes/{round_num}")
        assert rv.status_code == 200
        sample_size_options = json.loads(rv.data)["sampleSizes"]
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {
                "roundNum": round_num,
                "sampleSizes": {
                    contest_id: options[0]
                    for contest_id, options in sample_size_options.items()
                },
            },
        )
        assert_ok(rv)
        rounds = json.loads(client.get(f"/api/election/{election_id}/round").data)[
            "rounds"
        ]
        return rounds[-1]["id"]

    # 4. Round 1: submit Alice→Bob shift (Alice 70/Bob 25 instead of 80/15)
    #    on every sampled batch.
    round_1_id = start_round(1)
    submit_batch_results(
        round_1_id,
        {choice_ids[0]: 70, choice_ids[1]: 25, choice_ids[2]: 3, choice_ids[3]: 2},
    )
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    round_1_contest = RoundContest.query.filter_by(round_id=round_1_id).one()
    assert round_1_contest.is_complete is False, (
        f"Round 1 should fail because the threshold pair can't absorb the "
        f"Alice→Bob discrepancies (p-value: {round_1_contest.end_p_value})"
    )

    # 5. Round 2: submit clean results on the newly sampled batches.
    round_2_id = start_round(2)
    submit_batch_results(
        round_2_id,
        {choice_ids[0]: 80, choice_ids[1]: 15, choice_ids[2]: 3, choice_ids[3]: 2},
    )
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    round_2_contest = RoundContest.query.filter_by(round_id=round_2_id).one()
    assert round_2_contest.is_complete is True, (
        f"Round 2 should clear once additional clean batches are sampled "
        f"(p-value: {round_2_contest.end_p_value})"
    )

    # 6. Report: completed audit shows Majority received (the reported tallies
    #    say so; the audit confirmed it via round 2).
    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    report_csv = rv.data.decode("utf-8")
    assert "Subject to runoff law" in report_csv
    assert "Majority received, no runoff required" in report_csv
