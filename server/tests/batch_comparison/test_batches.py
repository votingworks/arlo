from typing import List
import io
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import

J1_BATCHES_ROUND_1 = 3
J2_BATCHES_ROUND_1 = 1


def test_list_batches_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches"
    )
    assert rv.status_code == 404


def test_list_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J1_BATCHES_ROUND_1
    compare_json(
        batches[0],
        {
            "id": assert_is_id,
            "lastEditedBy": None,
            "name": "Batch 1",
            "numBallots": 500,
            "resultTallySheets": [],
        },
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    compare_json(
        batches[0],
        {
            "id": assert_is_id,
            "lastEditedBy": None,
            "name": "Batch 1",
            "numBallots": 500,
            "resultTallySheets": [],
        },
    )


def test_batch_retrieval_list_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches/retrieval-list"
    )
    assert rv.status_code == 404


# Note: round 2 retrieval list tested in test_batch_comparison.py
def test_batch_retrieval_list_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    assert rv.status_code == 200
    assert (
        scrub_datetime(rv.headers["Content-Disposition"])
        == 'attachment; filename="batch-retrieval-J1-Test-Audit-test-batch-retrieval-list-round-1-DATETIME.csv"'
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert len(retrieval_list.splitlines()) == J1_BATCHES_ROUND_1 + 1
    snapshot.assert_match(retrieval_list)


def test_record_batch_results(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    tally_entry_user_id: str,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    # Record results for first jurisdiction
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J1_BATCHES_ROUND_1
    round_1_batch_ids = {batch["id"] for batch in batches}
    for batch in batches:
        assert batch["resultTallySheets"] == []
        assert batch["lastEditedBy"] is None

    results = {
        batches[0]["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[1]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[2]["id"]: {choice_ids[0]: 0, choice_ids[1]: 50, choice_ids[2]: 20,},
    }
    for batch_id, result in results.items():
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
            [{"name": "Tally Sheet #1", "results": result}],
        )
        assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    resp = json.loads(rv.data)
    batches = resp["batches"]
    for batch in batches:
        assert batch["resultTallySheets"] == [
            {"name": "Tally Sheet #1", "results": results[batch["id"]]}
        ]
        assert batch["lastEditedBy"] == default_ja_email(election_id)
    assert resp["resultsFinalizedAt"] is None

    # Update results for one batch
    updated_batch_2_results = {
        choice_ids[0]: 10,
        choice_ids[1]: 50,
        choice_ids[2]: 40,
    }
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[2]['id']}/results",
        [{"name": "Tally Sheet #1", "results": updated_batch_2_results}],
    )
    assert_ok(rv)

    # Finalize results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    resp = json.loads(rv.data)
    batches = resp["batches"]
    assert batches[2]["resultTallySheets"] == [
        {"name": "Tally Sheet #1", "results": updated_batch_2_results}
    ]
    assert batches[2]["lastEditedBy"] == default_ja_email(election_id)
    assert resp["resultsFinalizedAt"] is not None

    # Round shouldn't be over yet, since we haven't recorded results for all jurisdictions with sampled batches
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is None

    # Record results for the other jurisdiction using a tally entry account
    set_logged_in_user(client, UserType.TALLY_ENTRY, tally_entry_user_id)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J2_BATCHES_ROUND_1

    # Use multiple tally sheets this time
    for batch in batches:
        tally_sheets = [
            {
                "name": "Tally Sheet #1",
                "results": {choice_ids[0]: 100, choice_ids[1]: 25, choice_ids[2]: 40,},
            },
            {
                "name": "Tally Sheet #2",
                "results": {choice_ids[0]: 300, choice_ids[1]: 25, choice_ids[2]: 0,},
            },
        ]
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{batch['id']}/results",
            tally_sheets,
        )
        assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert batches[0]["resultTallySheets"] == tally_sheets
    assert batches[0]["lastEditedBy"] == "Alice, Bob"

    # Finalize results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Round should be over
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round"
    )
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None

    snapshot.assert_match(
        {
            f"{result.contest.name} - {result.contest_choice.name}": result.result
            for result in RoundContestResult.query.filter_by(round_id=round_1_id).all()
        }
    )

    # Start a new round to test round 2
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round"
    )
    assert rv.status_code == 200
    rounds = json.loads(rv.data)["rounds"]
    round_2_id = rounds[1]["id"]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == 2
    # Batches that were sampled in round 1 should be filtered out
    for batch in batches:
        assert batch["id"] not in round_1_batch_ids


def test_record_batch_results_as_support_user(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    batch = batches[0]
    assert batch["resultTallySheets"] == []
    assert batch["lastEditedBy"] is None

    results = {choice_ids[0]: 1, choice_ids[1]: 2, choice_ids[2]: 3}
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch['id']}/results",
        [{"name": "Sheet 1", "results": results}],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    resp = json.loads(rv.data)
    batches = resp["batches"]
    batch = batches[0]
    assert batch["resultTallySheets"] == [{"name": "Sheet 1", "results": results}]
    assert batch["lastEditedBy"] == DEFAULT_SUPPORT_EMAIL


def test_batch_tally_sheet_order(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    batch_id = batches[0]["id"]
    tally_sheets = [
        {
            "name": "AAA",
            "results": {choice_ids[0]: 1, choice_ids[1]: 1, choice_ids[2]: 1},
        },
        {
            "name": "BBB",
            "results": {choice_ids[0]: 1, choice_ids[1]: 1, choice_ids[2]: 1},
        },
    ]

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
        tally_sheets,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert batches[0]["resultTallySheets"] == tally_sheets
    assert batches[0]["lastEditedBy"] == default_ja_email(election_id)

    # ZZZ should stay at the front, not get sorted to the back (since the
    # natural sort order seems to be based on the unique index on tally sheet
    # name)
    tally_sheets = [
        {
            "name": "ZZZ",
            "results": {choice_ids[0]: 1, choice_ids[1]: 1, choice_ids[2]: 1},
        }
    ] + tally_sheets
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
        tally_sheets,
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert batches[0]["resultTallySheets"] == tally_sheets
    assert batches[0]["lastEditedBy"] == default_ja_email(election_id)


def test_record_batch_results_invalid(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    invalid_results = [
        ({}, "{} is not of type 'array'"),
        ([{"name": "Tally Sheet #1", "results": None}], "None is not of type 'object'"),
        ([{"name": "Tally Sheet #1", "results": {}}], "Invalid choice ids"),
        (
            [{"name": "Tally Sheet #1", "results": {"not-a-real-id": 0}}],
            "Invalid choice ids",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 0 for choice_id in choice_ids[:1]},
                }
            ],
            "Invalid choice ids",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: "not a number" for choice_id in choice_ids},
                }
            ],
            "'not a number' is not of type 'integer'",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: -1 for choice_id in choice_ids},
                }
            ],
            "-1 is less than the minimum of 0",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 400 for choice_id in choice_ids},
                }
            ],
            "Total votes for batch Batch 1 should not exceed 1000 - the number of ballots in the batch (500) times the number of votes allowed (2).",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 100 for choice_id in choice_ids},
                },
                {
                    "name": "Tally Sheet #2",
                    "results": {choice_id: 300 for choice_id in choice_ids},
                },
            ],
            "Total votes for batch Batch 1 should not exceed 1000 - the number of ballots in the batch (500) times the number of votes allowed (2).",
        ),
        (
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 1 for choice_id in choice_ids},
                },
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 3 for choice_id in choice_ids},
                },
            ],
            "Tally sheet names must be unique. 'Tally Sheet #1' has already been used.",
        ),
        (
            [{"results": {choice_id: 1 for choice_id in choice_ids}}],
            "'name' is a required property",
        ),
        ([{"name": "Tally Sheet #1"}], "'results' is a required property",),
        (
            [{"name": "", "results": {choice_id: 1 for choice_id in choice_ids},}],
            "'' is too short",
        ),
        (
            [{"name": 1, "results": {choice_id: 1 for choice_id in choice_ids},}],
            "1 is not of type 'string'",
        ),
    ]

    for invalid_result, expected_error in invalid_results:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
            invalid_result,
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_error}]
        }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/not-a-real-id/results",
        {},
    )
    assert rv.status_code == 404


def test_unfinalize_batch_results(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    for batch in batches:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch['id']}/results",
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 0 for choice_id in choice_ids},
                }
            ],
        )
        assert_ok(rv)

    # Can't unfinalize before finalizing
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have not been finalized",}
        ]
    }

    # Finalize
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )

    # Can't record more results after finalizing
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
        {choice_id: 0 for choice_id in choice_ids},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have already been finalized",}
        ]
    }

    # Can't finalize again after finalizing
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Results have already been finalized",}
        ]
    }

    # Unfinalize
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Now can record results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": {choice_id: 0 for choice_id in choice_ids},
            }
        ],
    )
    assert_ok(rv)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Finish the round
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    for batch in batches:
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{batch['id']}/results",
            [
                {
                    "name": "Tally Sheet #1",
                    "results": {choice_id: 0 for choice_id in choice_ids},
                }
            ],
        )
        assert_ok(rv)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Can't unfinalize after round ends
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.delete(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Results cannot be unfinalized after the audit round ends",
            }
        ]
    }


def test_record_batch_results_bad_round(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]

    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
        )
        assert rv.status_code == 200
        batches = json.loads(rv.data)["batches"]
        for batch in batches:
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/{batch['id']}/results",
                [
                    {
                        "name": "Tally Sheet #1",
                        "results": {choice_id: 0 for choice_id in choice_ids},
                    }
                ],
            )
            assert_ok(rv)
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize",
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Try a batch from the previous round
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches/{batches[0]['id']}/results",
        {choice_id: 0 for choice_id in choice_ids},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Batch was already audited in a previous round",
            }
        ]
    }

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
        {choice_id: 0 for choice_id in choice_ids},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Round 1 is not the current round"}
        ]
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-round-id/batches/{batches[0]['id']}/results",
        {choice_id: 0 for choice_id in choice_ids},
    )
    assert rv.status_code == 404

    # Hackily set the round's election id to be a different election to test
    # that we correctly check the round and election match
    round = Round.query.get(round_1_id)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id_2 = create_election(client, "Other Election", organization_id=org_id)
    round.election_id = election_id_2
    db_session.add(round)
    db_session.commit()

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
        {choice_id: 0 for choice_id in choice_ids},
    )
    assert rv.status_code == 404


def test_batches_human_sort_order(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    human_ordered_batches = [
        "Batch 1",
        "Batch 1 - 1",
        "Batch 1 - 2",
        "Batch 1 - 10",
        "Batch 2",
        "Batch 10",
    ]

    # Set contests
    contest_id = str(uuid.uuid4())
    contests = [
        {
            "id": contest_id,
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": len(human_ordered_batches) * 10 * 2,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": len(human_ordered_batches) * 5 * 2,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": len(human_ordered_batches) * 5 * 2,
                },
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Upload a manifest with mixed text/number batch names
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        (
                            "Batch Name,Number of Ballots\n"
                            + "\n".join(
                                f"{batch},20" for batch in human_ordered_batches
                            )
                        ).encode()
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)

        # Upload batch tallies
        batch_tallies_file = (
            "Batch Name,candidate 1,candidate 2,candidate 3\n"
            + "\n".join(f"{batch},10,5,5" for batch in human_ordered_batches)
        )
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
            data={
                "batchTallies": (
                    io.BytesIO(batch_tallies_file.encode()),
                    "batchTallies.csv",
                )
            },
        )
        assert_ok(rv)
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batch-tallies",
        )

    # Start round 1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_id: sample_size_options[contest_id][0]},
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    # Check that the batches are ordered in human order
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    assert rv.status_code == 200
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]

    def unique_preserve_order(values):
        return list(dict.fromkeys(values))

    unique_batches = unique_preserve_order(batch["name"] for batch in batches)
    assert unique_batches == [
        batch for batch in human_ordered_batches if batch in unique_batches
    ]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/report"
    )
    assert_match_report(rv.data, snapshot)


def test_finalize_batch_results_incomplete(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Don't record results for one batch
    results = {
        batches[0]["id"]: {choice_ids[0]: 400, choice_ids[1]: 50, choice_ids[2]: 40,},
        batches[1]["id"]: {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 40,},
    }
    for batch_id, result in results.items():
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
            [{"name": "Tally Sheet #1", "results": result}],
        )
        assert_ok(rv)

    # Finalize results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Cannot finalize batch results until all batches have audit results recorded.",
            }
        ]
    }
