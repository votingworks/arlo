from typing import Dict, List
import pytest
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Candidate 1", "numVotes": 750},
                {"id": str(uuid.uuid4()), "name": "Candidate 2", "numVotes": 250},
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Candidate 3", "numVotes": 450},
                {"id": str(uuid.uuid4()), "name": "Candidate 4", "numVotes": 50},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": [jurisdiction_ids[0]],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    manifests_by_jurisdiction = {
        jurisdiction_ids[0]: io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,100\n"
            b"Batch 2,100\n"
            b"Batch 3,100\n"
            b"Batch 4,100\n"
            b"Batch 5,100\n"
            b"Batch 6,100\n"
            b"Batch 7,100\n"
            b"Batch 8,100\n"
            b"Batch 9,100\n"
            b"Batch 10,100\n"
        ),
        jurisdiction_ids[1]: io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,100\n"
            b"Batch 2,50\n"
            b"Batch 3,50\n"
            b"Batch 4,50\n"
        ),
        jurisdiction_ids[2]: io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,100\n"
            b"Batch 2,50\n"
            b"Batch 3,50\n"
            b"Batch 4,50\n"
        ),
    }
    for jurisdiction_id, manifest in manifests_by_jurisdiction.items():
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    manifest,
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)


VALID_BATCH_TALLIES = [
    # Jurisdiction 1
    b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4\n"
    b"Batch 1,50,0,50,0\n"
    b"Batch 2,50,0,50,0\n"
    b"Batch 3,50,0,50,0\n"
    b"Batch 4,50,0,50,0\n"
    b"Batch 5,50,0,50,0\n"
    b"Batch 6,50,0,50,0\n"
    b"Batch 7,50,0,50,0\n"
    b"Batch 8,50,0,50,0\n"
    b"Batch 9,50,0,25,25\n"
    b"Batch 10,0,50,25,25\n",
    # Jurisdiction 2
    b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2\n"
    b"Batch 1,75,25\n"
    b"Batch 2,25,25\n"
    b"Batch 3,25,25\n"
    b"Batch 4,25,25\n",
    # Jurisdiction 3
    b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2\n"
    b"Batch 1,75,25\n"
    b"Batch 2,25,25\n"
    b"Batch 3,25,25\n"
    b"Batch 4,25,25\n",
]


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    batch_tallies_by_jurisdiction = {
        jurisdiction_ids[0]: io.BytesIO(VALID_BATCH_TALLIES[0]),
        jurisdiction_ids[1]: io.BytesIO(VALID_BATCH_TALLIES[1]),
        jurisdiction_ids[2]: io.BytesIO(VALID_BATCH_TALLIES[2]),
    }
    for (
        jurisdiction_id,
        batch_tallies_file,
    ) in batch_tallies_by_jurisdiction.items():
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
            data={
                "batchTallies": (
                    batch_tallies_file,
                    "batchTallies.csv",
                )
            },
        )
        assert_ok(rv)


def put_batch_results(
    client: FlaskClient,
    election_id: str,
    jurisdiction_id: str,
    round_id: str,
    batch_id: str,
    results: List[Dict[str, int]],
):
    return put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches/{batch_id}/results",
        [
            {"name": f"Tally Sheet #{i}", "results": sheet_results}
            for i, sheet_results in enumerate(results)
        ],
    )


def test_multi_contest_batch_comparison_jurisdiction_upload_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    test_cases = [
        # Success cases
        (jurisdiction_ids[0], io.BytesIO(VALID_BATCH_TALLIES[0]), None),
        (jurisdiction_ids[1], io.BytesIO(VALID_BATCH_TALLIES[1]), None),
        (jurisdiction_ids[2], io.BytesIO(VALID_BATCH_TALLIES[2]), None),
        # Error cases
        (
            jurisdiction_ids[0],
            # Missing contest 2 columns for jurisdiction with both contests
            io.BytesIO(b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2\n"),
            "Missing required columns: Contest 2 - Candidate 3, Contest 2 - Candidate 4.",
        ),
        (
            jurisdiction_ids[0],
            # Missing contest 1 columns for jurisdiction with both contests
            io.BytesIO(b"Batch Name,Contest 2 - Candidate 3,Contest 2 - Candidate 4\n"),
            "Missing required columns: Contest 1 - Candidate 1, Contest 1 - Candidate 2.",
        ),
        (
            jurisdiction_ids[0],
            # Extra column
            io.BytesIO(
                b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4,Contest 2 - Candidate 5\n"
            ),
            "Found unexpected columns. Allowed columns: Batch Name, Contest 1 - Candidate 1, Contest 1 - Candidate 2, Contest 2 - Candidate 3, Contest 2 - Candidate 4.",
        ),
        (
            jurisdiction_ids[0],
            # Missing contest name in contest choice CSV headers
            io.BytesIO(b"Batch Name,Candidate 1,Candidate 2,Candidate 3,Candidate 4\n"),
            "Missing required columns: Contest 1 - Candidate 1, Contest 1 - Candidate 2, Contest 2 - Candidate 3, Contest 2 - Candidate 4.",
        ),
        (
            jurisdiction_ids[1],
            # Missing contest 1 column for jurisdiction with only contest 1
            io.BytesIO(b"Batch Name,Contest 1 - Candidate 1\n"),
            "Missing required column: Contest 1 - Candidate 2.",
        ),
        (
            jurisdiction_ids[1],
            # Including contest 2 columns for jurisdiction with only contest 1
            io.BytesIO(
                b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4\n"
            ),
            "Found unexpected columns. Allowed columns: Batch Name, Contest 1 - Candidate 1, Contest 1 - Candidate 2.",
        ),
        (
            jurisdiction_ids[0],
            # Too many votes for contest 1
            io.BytesIO(
                b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4\n"
                b"Batch 1,100,1,0,0\n"
                b"Batch 2,0,0,0,0\n"
                b"Batch 3,0,0,0,0\n"
                b"Batch 4,0,0,0,0\n"
                b"Batch 5,0,0,0,0\n"
                b"Batch 6,0,0,0,0\n"
                b"Batch 7,0,0,0,0\n"
                b"Batch 8,0,0,0,0\n"
                b"Batch 9,0,0,0,0\n"
                b"Batch 10,0,0,0,0\n"
            ),
            'The total votes for contest "Contest 1" in batch "Batch 1" (101 votes) cannot exceed 100 - '
            "the number of ballots from the manifest (100 ballots) "
            "multiplied by the number of votes allowed for the contest (1 vote per ballot).",
        ),
        (
            jurisdiction_ids[0],
            # Too many votes for contest 2
            io.BytesIO(
                b"Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4\n"
                b"Batch 1,0,0,200,1\n"
                b"Batch 2,0,0,0,0\n"
                b"Batch 3,0,0,0,0\n"
                b"Batch 4,0,0,0,0\n"
                b"Batch 5,0,0,0,0\n"
                b"Batch 6,0,0,0,0\n"
                b"Batch 7,0,0,0,0\n"
                b"Batch 8,0,0,0,0\n"
                b"Batch 9,0,0,0,0\n"
                b"Batch 10,0,0,0,0\n"
            ),
            'The total votes for contest "Contest 2" in batch "Batch 1" (201 votes) cannot exceed 200 - '
            "the number of ballots from the manifest (100 ballots) "
            "multiplied by the number of votes allowed for the contest (2 votes per ballot).",
        ),
    ]

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    for jurisdiction_id, batch_tallies_file, expected_error in test_cases:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
            data={
                "batchTallies": (
                    batch_tallies_file,
                    "batchTallies.csv",
                )
            },
        )
        assert_ok(rv)

        rv = client.get(f"/api/election/{election_id}/jurisdiction")
        assert rv.status_code == 200
        jurisdictions = json.loads(rv.data)["jurisdictions"]
        jurisdiction = [j for j in jurisdictions if j["id"] == jurisdiction_id][0]
        batch_tallies_status = jurisdiction["batchTallies"]["processing"]

        if expected_error is None:
            assert batch_tallies_status["status"] == "PROCESSED"
            assert batch_tallies_status["error"] is None
        else:
            assert batch_tallies_status["status"] == "ERRORED"
            assert batch_tallies_status["error"] == expected_error


def test_multi_contest_batch_comparison_batch_results_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    contest_1_choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    contest_2_choice_ids = [choice["id"] for choice in contests[1]["choices"]]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    jurisdiction_1_batches = json.loads(rv.data)["batches"]
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    jurisdiction_2_batches = json.loads(rv.data)["batches"]

    test_cases = [
        # Success cases
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [
                {
                    contest_1_choice_ids[0]: 0,
                    contest_1_choice_ids[1]: 0,
                    contest_2_choice_ids[0]: 0,
                    contest_2_choice_ids[1]: 0,
                }
            ],
            None,
        ),
        (
            jurisdiction_ids[1],
            jurisdiction_1_batches[1]["id"],
            [{contest_1_choice_ids[0]: 0, contest_1_choice_ids[1]: 0}],
            None,
        ),
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [
                # Multiple tally sheets
                {
                    contest_1_choice_ids[0]: 25,
                    contest_1_choice_ids[1]: 25,
                    contest_2_choice_ids[0]: 25,
                    contest_2_choice_ids[1]: 25,
                },
                {
                    contest_1_choice_ids[0]: 25,
                    contest_1_choice_ids[1]: 25,
                    contest_2_choice_ids[0]: 25,
                    contest_2_choice_ids[1]: 25,
                },
            ],
            None,
        ),
        # Error cases
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [{"non-existent-choice-id": 0}],
            "Invalid choice ids",
        ),
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [{contest_1_choice_ids[0]: 0}],
            "Missing choice ids",
        ),
        (
            jurisdiction_ids[1],
            jurisdiction_2_batches[0]["id"],
            [
                {
                    contest_1_choice_ids[0]: 0,
                    contest_1_choice_ids[1]: 0,
                    # Contest 2 not relevant for this jurisdiction
                    contest_2_choice_ids[0]: 0,
                    contest_2_choice_ids[1]: 0,
                }
            ],
            "Invalid choice ids",
        ),
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [
                {
                    contest_1_choice_ids[0]: 100,
                    contest_1_choice_ids[1]: 1,
                    contest_2_choice_ids[0]: 0,
                    contest_2_choice_ids[1]: 0,
                }
            ],
            "Total votes for batch Batch 1 contest Contest 1 should not exceed 100 - "
            "the number of ballots in the batch (100) times the number of votes allowed (1).",
        ),
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [
                {
                    contest_1_choice_ids[0]: 0,
                    contest_1_choice_ids[1]: 0,
                    contest_2_choice_ids[0]: 200,
                    contest_2_choice_ids[1]: 1,
                }
            ],
            "Total votes for batch Batch 1 contest Contest 2 should not exceed 200 - "
            "the number of ballots in the batch (100) times the number of votes allowed (2).",
        ),
        (
            jurisdiction_ids[0],
            jurisdiction_1_batches[0]["id"],
            [
                # Multiple tally sheets
                {
                    contest_1_choice_ids[0]: 100,
                    contest_1_choice_ids[1]: 0,
                    contest_2_choice_ids[0]: 0,
                    contest_2_choice_ids[1]: 0,
                },
                {
                    contest_1_choice_ids[0]: 1,
                    contest_1_choice_ids[1]: 0,
                    contest_2_choice_ids[0]: 0,
                    contest_2_choice_ids[1]: 0,
                },
            ],
            "Total votes for batch Batch 1 contest Contest 1 should not exceed 100 - "
            "the number of ballots in the batch (100) times the number of votes allowed (1).",
        ),
    ]

    for jurisdiction_id, batch_id, batch_results, expected_error_message in test_cases:
        rv = put_batch_results(
            client,
            election_id,
            jurisdiction_id,
            round_1_id,
            batch_id,
            batch_results,
        )
        if expected_error_message is None:
            assert_ok(rv)
        else:
            assert rv.status_code == 400
            assert json.loads(rv.data)["errors"][0]["message"] == expected_error_message


def test_multi_contest_batch_comparison_end_to_end(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    #
    # Check jurisdictions
    #

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert [
        jurisdiction["batchTallies"]["numBallots"] for jurisdiction in jurisdictions
    ] == [500, 250, 250]

    #
    # Start audit
    #

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 2
    assert sample_size_options[contest_ids[0]][0]["size"] == 10
    assert sample_size_options[contest_ids[1]][0]["size"] == 8

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_ids[0]: sample_size_options[contest_ids[0]][0],
                contest_ids[1]: sample_size_options[contest_ids[1]][0],
            },
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    #
    # Check sampled batches
    #

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    jurisdiction_1_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_1_batches] == [
        "Batch 1",
        "Batch 2",
        "Batch 3",
        "Batch 5",
        "Batch 6",
        "Batch 7",
        "Batch 9",
    ]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    jurisdiction_2_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_2_batches] == ["Batch 1"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/batches"
    )
    jurisdiction_3_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_3_batches] == ["Batch 1"]

    # Since batches can be drawn multiple times, count the underlying batch draws rather than the
    # batches returned above
    for contest_index in [0, 1]:
        batch_draws = SampledBatchDraw.query.filter_by(
            round_id=round_1_id, contest_id=contest_ids[contest_index]
        ).all()
        expected_num_batch_draws = sample_size_options[contest_ids[contest_index]][0][
            "size"
        ]
        assert len(batch_draws) == expected_num_batch_draws

    #
    # Enter batch results
    #

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    contest_1_choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    contest_2_choice_ids = [choice["id"] for choice in contests[1]["choices"]]

    # Enter jurisdiction 1 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    reported_results_for_batches_1_through_8 = {
        contest_1_choice_ids[0]: 50,
        contest_1_choice_ids[1]: 0,
        contest_2_choice_ids[0]: 50,
        contest_2_choice_ids[1]: 0,
    }
    jurisdiction_1_batch_results = {
        # Batch 1 (with no discrepancies)
        jurisdiction_1_batches[0]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 2 (with no discrepancies)
        jurisdiction_1_batches[1]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 3 (with no discrepancies)
        jurisdiction_1_batches[2]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 5 (with no discrepancies)
        jurisdiction_1_batches[3]["id"]: [
            # Multiple tally sheets
            {
                contest_1_choice_ids[0]: 25,
                contest_1_choice_ids[1]: 0,
                contest_2_choice_ids[0]: 25,
                contest_2_choice_ids[1]: 0,
            },
            {
                contest_1_choice_ids[0]: 25,
                contest_1_choice_ids[1]: 0,
                contest_2_choice_ids[0]: 25,
                contest_2_choice_ids[1]: 0,
            },
        ],
        # Batch 6 (with contest 1 discrepancy)
        jurisdiction_1_batches[4]["id"]: [
            {
                contest_1_choice_ids[0]: 49,
                contest_1_choice_ids[1]: 1,
                contest_2_choice_ids[0]: 50,
                contest_2_choice_ids[1]: 0,
            }
        ],
        # Batch 7 (with contest 2 discrepancy)
        jurisdiction_1_batches[5]["id"]: [
            {
                contest_1_choice_ids[0]: 50,
                contest_1_choice_ids[1]: 0,
                contest_2_choice_ids[0]: 49,
                contest_2_choice_ids[1]: 1,
            }
        ],
        # Batch 9 (with contest 1 and contest 2 discrepancies)
        jurisdiction_1_batches[6]["id"]: [
            {
                contest_1_choice_ids[0]: 52,
                contest_1_choice_ids[1]: 0,
                contest_2_choice_ids[0]: 26,
                contest_2_choice_ids[1]: 24,
            }
        ],
    }
    for batch_id, results in jurisdiction_1_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[0], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Get jurisdiction admin report
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)

    # Get audit admin report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Enter jurisdiction 2 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    jurisdiction_2_batch_results = {
        # Batch 1 (with no discrepancies)
        jurisdiction_2_batches[0]["id"]: [
            {contest_1_choice_ids[0]: 75, contest_1_choice_ids[1]: 25}
        ],
    }
    for batch_id, results in jurisdiction_2_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[1], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Enter jurisdiction 3 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )

    jurisdiction_3_batch_results = {
        # Batch 1 (with contest 1 discrepancy)
        jurisdiction_3_batches[0]["id"]: [
            {
                contest_1_choice_ids[0]: 74,
                contest_1_choice_ids[1]: 26,
            }
        ],
    }
    for batch_id, results in jurisdiction_3_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[2], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check discrepancy counts
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-counts")
    discrepancy_counts = json.loads(rv.data)
    assert discrepancy_counts[jurisdictions[0]["id"]] == 4
    assert discrepancy_counts[jurisdictions[1]["id"]] == 0
    assert discrepancy_counts[jurisdictions[2]["id"]] == 1

    #
    # Finish audit
    #

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["isAuditComplete"]

    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)


def test_multi_contest_batch_comparison_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    round_1_id: str,
    snapshot,
):
    #
    # Check sampled batches
    #

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    jurisdiction_1_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_1_batches] == [
        "Batch 1",
        "Batch 2",
        "Batch 3",
        "Batch 5",
        "Batch 6",
        "Batch 7",
        "Batch 9",
    ]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    jurisdiction_2_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_2_batches] == ["Batch 1"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/batches"
    )
    jurisdiction_3_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_3_batches] == ["Batch 1"]

    #
    # Enter batch results
    #

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    contest_1_choice_ids = [choice["id"] for choice in contests[0]["choices"]]
    contest_2_choice_ids = [choice["id"] for choice in contests[1]["choices"]]

    # Enter jurisdiction 1 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    reported_results_for_batches_1_through_8 = {
        contest_1_choice_ids[0]: 50,
        contest_1_choice_ids[1]: 0,
        contest_2_choice_ids[0]: 50,
        contest_2_choice_ids[1]: 0,
    }
    jurisdiction_1_batch_results = {
        # Batch 1 (with no discrepancies)
        jurisdiction_1_batches[0]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 2 (with no discrepancies)
        jurisdiction_1_batches[1]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 3 (with no discrepancies)
        jurisdiction_1_batches[2]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 5 (with no discrepancies)
        jurisdiction_1_batches[3]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 6 (with no discrepancies)
        jurisdiction_1_batches[4]["id"]: [reported_results_for_batches_1_through_8],
        # Batch 7 (with large contest 1 discrepancy)
        jurisdiction_1_batches[5]["id"]: [
            {
                contest_1_choice_ids[0]: 0,
                contest_1_choice_ids[1]: 50,
                contest_2_choice_ids[0]: 50,
                contest_2_choice_ids[1]: 0,
            }
        ],
        # Batch 9 (with no discrepancies)
        jurisdiction_1_batches[6]["id"]: [
            {
                contest_1_choice_ids[0]: 50,
                contest_1_choice_ids[1]: 0,
                contest_2_choice_ids[0]: 25,
                contest_2_choice_ids[1]: 25,
            }
        ],
    }
    for batch_id, results in jurisdiction_1_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[0], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Enter jurisdiction 2 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    jurisdiction_2_batch_results = {
        # Batch 1 (with no discrepancies)
        jurisdiction_2_batches[0]["id"]: [
            {contest_1_choice_ids[0]: 75, contest_1_choice_ids[1]: 25}
        ],
    }
    for batch_id, results in jurisdiction_2_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[1], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Enter jurisdiction 3 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )

    jurisdiction_3_batch_results = {
        # Batch 1 (with no discrepancies)
        jurisdiction_3_batches[0]["id"]: [
            {contest_1_choice_ids[0]: 75, contest_1_choice_ids[1]: 25}
        ],
    }
    for batch_id, results in jurisdiction_3_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[2], round_1_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check discrepancy counts
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-counts")
    discrepancy_counts = json.loads(rv.data)
    assert discrepancy_counts[jurisdiction_ids[0]] == 1
    assert discrepancy_counts[jurisdiction_ids[1]] == 0
    assert discrepancy_counts[jurisdiction_ids[2]] == 0

    #
    # End round 1
    #

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    assert not rounds[0]["isAuditComplete"]

    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)

    #
    # Start round 2
    #

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    round_2_id = rounds[1]["id"]

    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)

    #
    # Check sampled batches
    #

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches"
    )
    jurisdiction_1_batches = json.loads(rv.data)["batches"]
    assert [batch["name"] for batch in jurisdiction_1_batches] == ["Batch 8"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_2_id}/batches"
    )
    jurisdiction_2_batches = json.loads(rv.data)["batches"]
    assert len(jurisdiction_2_batches) == 0

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_2_id}/batches"
    )
    jurisdiction_3_batches = json.loads(rv.data)["batches"]
    assert len(jurisdiction_3_batches) == 0

    #
    # Enter batch results
    #

    # Enter jurisdiction 1 batch results

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    jurisdiction_1_batch_results = {
        # Batch 8 (with no discrepancies)
        jurisdiction_1_batches[0]["id"]: [reported_results_for_batches_1_through_8],
    }
    for batch_id, results in jurisdiction_1_batch_results.items():
        rv = put_batch_results(
            client, election_id, jurisdiction_ids[0], round_2_id, batch_id, results
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches/finalize",
    )
    assert_ok(rv)

    # Enter jurisdiction 2 batch results (nothing to enter, just need to finalize)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_2_id}/batches/finalize",
    )
    assert_ok(rv)

    # Enter jurisdiction 3 batch results (nothing to enter, just need to finalize)

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, f"j3-{election_id}@example.com"
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[2]}/round/{round_2_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check discrepancy counts
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-counts")
    discrepancy_counts = json.loads(rv.data)
    assert discrepancy_counts[jurisdiction_ids[0]] == 0
    assert discrepancy_counts[jurisdiction_ids[1]] == 0
    assert discrepancy_counts[jurisdiction_ids[2]] == 0

    #
    # End round 2 / finish audit
    #

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[1]["isAuditComplete"]

    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    assert_match_report(rv.data, snapshot)


def test_multi_contest_batch_comparison_batch_tallies_template_csv_generation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids,  # pylint: disable=unused-argument
):
    for user_type, user_email in [
        (UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL),
        (UserType.JURISDICTION_ADMIN, default_ja_email(election_id)),
    ]:
        set_logged_in_user(client, user_type, user_email)

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies/template-csv"
        )
        assert rv.status_code == 200
        csv_contents = rv.data.decode("utf-8")
        assert csv_contents == (
            "Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4\r\n"
            "Batch 1,0,0,0,0\r\n"
            "Batch 2,0,0,0,0\r\n"
            "Batch 3,0,0,0,0\r\n"
        )

        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies/template-csv"
        )
        assert rv.status_code == 200
        csv_contents = rv.data.decode("utf-8")
        assert csv_contents == (
            "Batch Name,Contest 1 - Candidate 1,Contest 1 - Candidate 2\r\n"
            "Batch 1,0,0\r\n"
            "Batch 2,0,0\r\n"
            "Batch 3,0,0\r\n"
        )


def test_multi_contest_batch_comparison_batch_tallies_summed_by_jurisdiction_csv_generation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids,  # pylint: disable=unused-argument
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(
        f"/api/election/{election_id}/batch-tallies/summed-by-jurisdiction-csv"
    )
    assert rv.status_code == 200
    csv_contents = rv.data.decode("utf-8")
    print(csv_contents)
    assert csv_contents == (
        "Jurisdiction,Contest 1 - Candidate 1,Contest 1 - Candidate 2,Contest 2 - Candidate 3,Contest 2 - Candidate 4,Total Ballots\r\n"
        "J1,450,50,450,50,1000\r\n"
        "J2,150,100,,,250\r\n"
        "J3,150,100,,,250\r\n"
        "Total,750,250,450,50,1500\r\n"
    )


def test_multi_contest_batch_comparison_editing_contests_after_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids,  # pylint: disable=unused-argument
    contest_ids,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    contest1 = contests[0]
    contest2 = contests[1]
    del contest1["totalBallotsCast"]
    del contest2["totalBallotsCast"]

    # Delete contest 2
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest1])
    assert_ok(rv)

    # Verify that previously uploaded batch tallies are marked as no longer valid
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    for jurisdiction in jurisdictions:
        batch_tallies_status = jurisdiction["batchTallies"]["processing"]
        assert batch_tallies_status["status"] == "ERRORED"
        assert (
            batch_tallies_status["error"]
            == "Missing required columns: Candidate 1, Candidate 2."
        )

    # Recreate contest 2
    contest2["id"] = str(uuid.uuid4())
    contest2["choices"][0]["id"] = str(uuid.uuid4())
    contest2["choices"][1]["id"] = str(uuid.uuid4())
    rv = put_json(client, f"/api/election/{election_id}/contest", [contest1, contest2])
    assert_ok(rv)

    # Verify that previously uploaded batch tallies are marked as valid again
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    for jurisdiction in jurisdictions:
        batch_tallies_status = jurisdiction["batchTallies"]["processing"]
        assert batch_tallies_status["status"] == "PROCESSED"
        assert batch_tallies_status["error"] is None
