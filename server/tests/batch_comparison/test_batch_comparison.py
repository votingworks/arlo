import io
from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...util.group_by import group_by
from ...worker.bgcompute import bgcompute_update_batch_tallies_file


def test_batch_comparison_only_one_contest_allowed(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 6000},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 3500},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 3500},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 6000},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 3500},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 3500},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Batch comparison audits may only have one contest.",
            }
        ]
    }


def test_batch_comparison_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    snapshot.assert_match(sample_size_options[contest_id])


def test_batch_comparison_without_all_batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Some jurisdictions haven't uploaded their batch tallies files yet.",
            },
        },
    )


def test_batch_comparison_too_many_votes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,1000,0,0\n"  # Too many votes for candidate 1
        b"Batch 2,500,250,250\n"
        b"Batch 3,500,250,250\n"
        b"Batch 4,500,250,250\n"
        b"Batch 5,100,50,50\n"
        b"Batch 6,100,50,50\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies",
        data={"batchTallies": (io.BytesIO(batch_tallies_file), "batchTallies.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_batch_tallies_file(election_id)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert rv.status_code == 200
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Total votes in batch tallies files for contest choice candidate 1 (5200) is greater than the reported number of votes for that choice (5000).",
            },
        },
    )


def test_batch_comparison_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    # Check jurisdiction status before starting the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"] is None
    assert jurisdictions[1]["currentRoundStatus"] is None

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Use an artificially large sample size in order to have enough samples to work with
    sample_size = 15
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: {"key": "custom", "size": sample_size, "prob": None}
            },
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    compare_json(
        rounds,
        [
            {
                "id": assert_is_id,
                "roundNum": 1,
                "startedAt": assert_is_date,
                "endedAt": None,
                "isAuditComplete": None,
                "sampledAllBallots": False,
                "drawSampleTask": {
                    "status": "PROCESSED",
                    "startedAt": assert_is_date,
                    "completedAt": assert_is_date,
                    "error": None,
                },
            }
        ],
    )

    # Check jurisdiction status after starting the round
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(round_contests) == 1
    assert round_contests[0]

    # Check that the batches got sampled
    batch_draws = SampledBatchDraw.query.filter_by(round_id=rounds[0]["id"]).all()
    assert len(batch_draws) == sample_size

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == set(jurisdiction_ids[:2])

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[0]['id']}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)

    # Check jurisdiction status moved to IN_PROGRESS
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "IN_PROGRESS"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "NOT_STARTED"

    # Check that the batches got divvied up evenly between the audit boards
    sampled_batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction_ids[0])
        .join(SampledBatchDraw)
        .filter_by(round_id=rounds[0]["id"])
        .all()
    )
    audit_board_batches = [
        [batch.id for batch in batches]
        for batches in group_by(
            sampled_batches, key=lambda batch: batch.audit_board_id
        ).values()
    ]
    assert len(audit_board_batches) == 3
    assert abs(len(audit_board_batches[0]) - len(audit_board_batches[1])) <= 1
    assert abs(len(audit_board_batches[1]) - len(audit_board_batches[2])) <= 1

    # And check that each batch got assigned to one and only one audit board
    assert sorted(
        list(set(batch_id for batches in audit_board_batches for batch_id in batches))
    ) == sorted(
        list(batch_id for batches in audit_board_batches for batch_id in batches)
    )


def test_batch_comparison_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Record some batch results
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    batch_results = {
        batches[0]["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[1]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[2]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 40,},
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    # Check jurisdiction status after recording results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Now do the second jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Record results for the second jurisdiction
    batch_results = {
        batches[0]["id"]: {choice_ids[0]: 100, choice_ids[1]: 100, choice_ids[2]: 40,}
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    # Check jurisdiction status after recording results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]

    # Check jurisdiction status after starting the new round
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check that we also created RoundContest objects
    round_contests = RoundContest.query.filter_by(round_id=rounds[1]["id"]).all()
    assert len(round_contests) == 1
    assert round_contests[0]

    # Check that we automatically select the sample size
    batch_draws = SampledBatchDraw.query.filter_by(round_id=rounds[1]["id"]).all()
    assert len(batch_draws) == 5

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == set(jurisdiction_ids[:2])

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[1]['id']}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    # Test the retrieval list correctly marks ballots that were sampled last round
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{rounds[1]['id']}/batches/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    # Test the audit reports
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)


def test_batch_comparison_custom_sample_size_validation(
    client: FlaskClient,
    election_id: str,
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    bad_sample_sizes = [
        (
            {contest_id: {"key": "bad_key", "size": 10, "prob": None}},
            "Invalid sample size key for contest Contest 1: bad_key",
        ),
        (
            {contest_id: {"key": "custom", "size": 25, "prob": None}},
            "Sample size for contest Contest 1 must be less than or equal to: 15 (the total number of batches in the contest)",
        ),
    ]
    for bad_sample_size, expected_error in bad_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {"roundNum": 1, "sampleSizes": bad_sample_size},
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"message": expected_error, "errorType": "Bad Request",}]
        }


def test_batch_comparison_batches_sampled_multiple_times(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Make sure some batches got sampled multiple times
    assert len(batches) < (
        SampledBatchDraw.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_ids[0])
        .count()
    )

    # Record batch results that match batch tallies exactly
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    batch_results = {
        # Batch 1
        batches[0]["id"]: {choice_ids[0]: 500, choice_ids[1]: 250, choice_ids[2]: 250,},
        # Batch 8
        batches[1]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 50,},
        # Batch 6
        batches[2]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 50,},
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    # Now do the second jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Record batch results that match batch tallies exactly
    batch_results = {
        # Batch 3
        batches[0]["id"]: {choice_ids[0]: 500, choice_ids[1]: 250, choice_ids[2]: 250,}
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/results",
        batch_results,
    )
    assert_ok(rv)

    # Audit should be complete
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None
    assert rounds[0]["isAuditComplete"] is True

    # Test the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
