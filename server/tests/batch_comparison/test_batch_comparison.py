import csv
import io
from typing import Dict, List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def parse_vote_deltas(
    vote_deltas: str, choices: List[dict]
) -> Optional[Dict[str, int]]:
    if vote_deltas == "":
        return None
    deltas = {
        choice_name: int(delta)
        for choice_name, delta in [
            delta.split(": ") for delta in vote_deltas.split("; ")
        ]
    }
    return {choice["name"]: deltas.get(choice["name"], 0) for choice in choices}


def check_discrepancies(
    report: str,
    expected_discrepancies: dict,
    choices: List[dict],
):
    report_batches = list(csv.DictReader(io.StringIO(report)))
    for jurisdiction_name, jurisdiction_discrepancies in expected_discrepancies.items():
        for batch_name, batch_discrepancies in jurisdiction_discrepancies.items():
            row = next(
                row
                for row in report_batches
                if row["Jurisdiction Name"] == jurisdiction_name
                and row["Batch Name"] == batch_name
            )
            assert (
                parse_vote_deltas(row["Change in Results: Contest 1"], choices)
                == batch_discrepancies
            ), f"Discrepancy mismatch for {(jurisdiction_name, batch_name)}"


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
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
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
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
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
    rv = upload_batch_tallies(
        client, io.BytesIO(batch_tallies_file), election_id, jurisdiction_ids[1]
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert rv.status_code == 200
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Total votes in batch tallies files for contest choice candidate 1 (5,200 votes) is greater than the reported number of votes for that choice (5,000 votes).",
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
    sample_size = 14
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
                "needsFullHandTally": False,
                "isFullHandTally": False,
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


def test_batch_comparison_round_2(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
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
    batch_results_j1 = {
        # Use multiple tally sheets to make sure they get aggregated correctly
        batches[0]["id"]: [
            {
                choice_ids[0]: 200,
                choice_ids[1]: 40,
                choice_ids[2]: 0,
            },
            {
                choice_ids[0]: 150,
                choice_ids[1]: 10,
                choice_ids[2]: 0,
            },
            {
                choice_ids[0]: 50,
                choice_ids[1]: 0,
                choice_ids[2]: 40,
            },
        ],
        batches[1]["id"]: [
            {
                choice_ids[0]: 400,
                choice_ids[1]: 50,
                choice_ids[2]: 40,
            }
        ],
        batches[2]["id"]: [
            {
                choice_ids[0]: 500,
                choice_ids[1]: 250,
                choice_ids[2]: 240,
            }
        ],
        batches[3]["id"]: [
            {
                choice_ids[0]: 100,
                choice_ids[1]: 50,
                choice_ids[2]: 40,
            }
        ],
        batches[4]["id"]: [
            {
                choice_ids[0]: 100,
                choice_ids[1]: 50,
                choice_ids[2]: 50,
            }
        ],
    }

    assert batches[0]["name"] == "Batch 1"
    assert batches[1]["name"] == "Batch 2"
    assert batches[2]["name"] == "Batch 4"
    assert batches[3]["name"] == "Batch 6"
    assert batches[4]["name"] == "Batch 8"
    # Batch tallies (from conftest.py)
    # Batch 1: 500,250,250
    # Batch 2: 500,250,250
    # Batch 4: 500,250,250
    # Batch 6: 100,50,50
    # Batch 8: 100,50,50
    expected_discrepancies_j1 = {
        "Batch 1": {"candidate 1": 100, "candidate 2": 200, "candidate 3": 210},
        "Batch 2": {"candidate 1": 100, "candidate 2": 200, "candidate 3": 210},
        "Batch 4": {"candidate 1": 0, "candidate 2": 0, "candidate 3": 10},
        "Batch 6": {"candidate 1": 0, "candidate 2": 0, "candidate 3": 10},
    }

    for i, (batch_id, results) in enumerate(batch_results_j1.items()):
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
            [
                {"name": f"Tally Sheet #{i}", "results": sheet_results}
                for i, sheet_results in enumerate(results)
            ],
        )
        assert_ok(rv)

        # Check jurisdiction status after recording results
        set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
        rv = client.get(f"/api/election/{election_id}/jurisdiction")
        jurisdictions = json.loads(rv.data)["jurisdictions"]
        assert jurisdictions[0]["currentRoundStatus"]["numSamplesAudited"] == i + 1
        snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])

    # Discrepancies should not show before the results are finalized
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert len(discrepancies) == 0

    # Finalize the results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check jurisdiction status after finalizing results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check discrepancies
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert (
        discrepancies[jurisdictions[0]["id"]]["Batch 1"][contests[0]["id"]][
            "reportedVotes"
        ][choice_ids[0]]
        == 500
    )
    assert (
        discrepancies[jurisdictions[0]["id"]]["Batch 1"][contests[0]["id"]][
            "auditedVotes"
        ][choice_ids[0]]
        == 400
    )
    assert (
        discrepancies[jurisdictions[0]["id"]]["Batch 1"][contests[0]["id"]][
            "discrepancies"
        ][choice_ids[0]]
        == 100
    )

    # Now do the second jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == 1

    batch_results_j2 = {
        batches[0]["id"]: {choice_ids[0]: 100, choice_ids[1]: 100, choice_ids[2]: 40}
    }

    assert batches[0]["name"] == "Batch 3"
    # Batch tallies
    # Batch 3,500,250,250
    expected_discrepancies_j2 = {
        "Batch 3": {"candidate 1": 400, "candidate 2": 150, "candidate 3": 210}
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{batches[0]['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": batch_results_j2[batches[0]["id"]],
            }
        ],
    )
    assert_ok(rv)

    # Check the discrepancy report - only the first jurisdiction should have
    # audit results so far since the second jurisdiction hasn't finalized yet
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    check_discrepancies(
        discrepancy_report, {"J1": expected_discrepancies_j1}, contests[0]["choices"]
    )
    for row in csv.DictReader(io.StringIO(discrepancy_report)):
        if row["Jurisdiction Name"] == "J2":
            assert row["Audited?"] == "No"
            assert row["Audit Results: Contest 1"] == ""
            assert row["Reported Results: Contest 1"] == ""
            assert row["Change in Results: Contest 1"] == ""
            assert row["Change in Margin: Contest 1"] == ""

    # Finalize the results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check jurisdiction status after recording results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Start a second round
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
    assert len(batch_draws) == 2

    # Check that we're sampling batches from the jurisdiction that uploaded manifests
    sampled_jurisdictions = {draw.batch.jurisdiction_id for draw in batch_draws}
    assert sampled_jurisdictions == set(jurisdiction_ids[:2])

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
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BATCHES ########\r\n")[1]
    )
    check_discrepancies(
        discrepancy_report,
        {"J1": expected_discrepancies_j1, "J2": expected_discrepancies_j2},
        contests[0]["choices"],
    )

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
            "errors": [
                {
                    "message": expected_error,
                    "errorType": "Bad Request",
                }
            ]
        }


def test_batch_comparison_batches_sampled_multiple_times(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    # Adjust random seed to one that we know will result in a sample with duplicates
    rv = client.get(f"/api/election/{election_id}/settings")
    election_settings = json.loads(rv.data)
    put_json(
        client,
        f"/api/election/{election_id}/settings",
        {**election_settings, "randomSeed": "0123"},
    )

    # Start the audit
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: sample_size_options_for_contest[0]
                for contest_id, sample_size_options_for_contest in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

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
    batch_results_j1 = {
        # Batch 1
        batches[0]["id"]: [
            # Use multiple tally sheets to make sure we aggregate them correctly
            # even when a batch is sampled multiple times
            {
                choice_ids[0]: 300,
                choice_ids[1]: 200,
                choice_ids[2]: 50,
            },
            {
                choice_ids[0]: 150,
                choice_ids[1]: 50,
                choice_ids[2]: 0,
            },
            {
                choice_ids[0]: 50,
                choice_ids[1]: 0,
                choice_ids[2]: 200,
            },
        ],
        # Batch 3
        batches[1]["id"]: [
            {
                choice_ids[0]: 500,
                choice_ids[1]: 250,
                choice_ids[2]: 250,
            }
        ],
        # Batch 4
        batches[2]["id"]: [
            {
                choice_ids[0]: 500,
                choice_ids[1]: 250,
                choice_ids[2]: 250,
            }
        ],
    }

    for batch_id, results in batch_results_j1.items():
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
            [
                {"name": f"Tally Sheet #{i}", "results": sheet_results}
                for i, sheet_results in enumerate(results)
            ],
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Now do the second jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]

    # Record batch results that match batch tallies exactly
    batch_results_j2 = {
        # Batch 1
        batches[0]["id"]: {
            choice_ids[0]: 500,
            choice_ids[1]: 250,
            choice_ids[2]: 250,
        },
        # Batch 5
        batches[1]["id"]: {
            choice_ids[0]: 300,
            choice_ids[1]: 100,
            choice_ids[2]: 100,
        },
    }

    for batch_id, sheet_results in batch_results_j2.items():
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{batch_id}/results",
            [{"name": "Tally Sheet #1", "results": sheet_results}],
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Check jurisdiction status
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check discrepancies
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert jurisdictions[0]["id"] not in discrepancies
    assert jurisdictions[1]["id"] not in discrepancies

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Audit should be complete
    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    assert rounds[0]["endedAt"] is not None
    assert rounds[0]["isAuditComplete"] is True

    # Test the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BATCHES ########\r\n")[1]
    )
    expected_discrepancies = {
        "J1": {"Batch 1": None, "Batch 3": None, "Batch 4": None},
        "J2": {"Batch 1": None, "Batch 5": None},
    }
    check_discrepancies(
        discrepancy_report,
        expected_discrepancies,
        contests[0]["choices"],
    )


def test_batch_comparison_sample_all_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    sample_size = (
        Batch.query.join(Jurisdiction).filter_by(election_id=election_id).count()
    )
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
    round_1_id = rounds[0]["id"]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    all_batches = []
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
        )
        assert rv.status_code == 200
        all_batches += json.loads(rv.data)["batches"]

    # Every batch should get sampled exactly once
    assert len(all_batches) == sample_size


def test_batch_comparison_undo_start_round_1(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data) == {"rounds": []}

    assert (
        SampledBatchDraw.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .count()
        == 0
    )


def test_batch_comparison_cant_create_audit_boards(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], round_1_id: str
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Batch comparison audits do not use audit boards",
            }
        ]
    }


def test_batch_comparison_sample_preview(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    contest_ids: List[str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Start computing a sample preview
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_ids[0]][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: sample_size}},
    )
    assert_ok(rv)

    # Check the computed sample preview
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    assert rv.status_code == 200
    sample_preview = json.loads(rv.data)
    compare_json(
        sample_preview["task"],
        {
            "status": "PROCESSED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": None,
        },
    )
    assert len(sample_preview["jurisdictions"]) == len(jurisdiction_ids)
    snapshot.assert_match(sample_preview["jurisdictions"])

    # Make sure it matches the sample drawn when we start a round
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    for i, jurisdiction in enumerate(jurisdictions):
        preview = sample_preview["jurisdictions"][i]
        assert preview["name"] == jurisdiction["name"]
        assert preview["numSamples"] == jurisdiction["currentRoundStatus"]["numSamples"]
        assert preview["numUnique"] == jurisdiction["currentRoundStatus"]["numUnique"]


def test_batch_tallies_summed_by_jurisdiction_csv_generation(
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
    assert csv_contents == (
        "Jurisdiction,candidate 1,candidate 2,candidate 3,Total Ballots\r\n"
        "J1,2500,1250,1250,2500\r\n"
        "J2,2500,1250,1250,2500\r\n"
        "J3,,,,\r\n"
        "Total,5000,2500,2500,5000\r\n"
    )


def test_batch_comparison_combined_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j1_sampled_batches_original = json.loads(rv.data)["batches"]

    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/batches")
    j1_all_batches = json.loads(rv.data)["batches"]

    # Combine some batches
    batch_3_unsampled = next(
        batch for batch in j1_all_batches if batch["name"] == "Batch 3"
    )
    assert batch_3_unsampled["id"] not in (
        sampled_batch["id"] for sampled_batch in j1_sampled_batches_original
    )
    batch_1_sampled = next(
        batch for batch in j1_all_batches if batch["name"] == "Batch 1"
    )
    assert batch_1_sampled["id"] in (
        sampled_batch["id"] for sampled_batch in j1_sampled_batches_original
    )
    batch_2_sampled = next(
        batch for batch in j1_all_batches if batch["name"] == "Batch 2"
    )
    assert batch_2_sampled["id"] in (
        sampled_batch["id"] for sampled_batch in j1_sampled_batches_original
    )
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        {
            "name": "Combined Batch",
            "subBatchIds": [
                batch_3_unsampled["id"],
                batch_1_sampled["id"],
                batch_2_sampled["id"],
            ],
        },
    )
    assert_ok(rv)

    # Now the jurisdiction should only see the combined batch
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    j1_sampled_batches = json.loads(rv.data)["batches"]
    assert len(j1_sampled_batches) == len(j1_sampled_batches_original) - 1
    combined_batch = next(
        batch for batch in j1_sampled_batches if batch["name"] == "Combined Batch"
    )
    sampled_batch_names = {batch["name"] for batch in j1_sampled_batches}
    assert batch_3_unsampled["name"] not in sampled_batch_names
    assert batch_1_sampled["name"] not in sampled_batch_names
    assert batch_2_sampled["name"] not in sampled_batch_names

    # Reported tallies from conftest.py:
    # Batch 1: 500,250,250
    # Batch 2: 500,250,250
    # Batch 3: 500,250,250
    reported_tallies = {
        choice_ids[0]: 500 + 500 + 500,
        choice_ids[1]: 250 + 250 + 250,
        choice_ids[2]: 250 + 250 + 250,
    }

    # Try to audit the combined batch with invalid tallies (check validation)
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{combined_batch['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": {
                    **reported_tallies,
                    choice_ids[0]: reported_tallies[choice_ids[0]] + 1,
                },
            }
        ],
    )
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Bad Request",
                "message": "Total votes for batch Combined Batch contest Contest 1 should not exceed 3000 - the number of ballots in the batch (1500) times the number of votes allowed (2).",
            }
        ]
    }

    # Audit the combined batch
    candidate_2_discrepancy = 5
    candidate_3_discrepancy = -5
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{combined_batch['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": {
                    **reported_tallies,
                    choice_ids[1]: reported_tallies[choice_ids[1]]
                    - candidate_2_discrepancy,
                    choice_ids[2]: reported_tallies[choice_ids[2]]
                    - candidate_3_discrepancy,
                },
            }
        ],
    )
    assert_ok(rv)

    # Audit the rest of the sampled batches correctly
    results = {
        "Batch 4": {choice_ids[0]: 500, choice_ids[1]: 250, choice_ids[2]: 250},
        "Batch 6": {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 50},
        "Batch 8": {choice_ids[0]: 100, choice_ids[1]: 50, choice_ids[2]: 50},
    }
    for batch in j1_sampled_batches:
        if batch["name"] == "Combined Batch":
            continue
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch['id']}/results",
            [
                {
                    "name": "Tally Sheet #1",
                    "results": results[batch["name"]],
                }
            ],
        )
        assert_ok(rv)

    # Finalize the results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )

    # Check discrepancies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    choices = contests[0]["choices"]
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "discrepancies"
        ][choices[0]["id"]]
        == 0
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "discrepancies"
        ][choices[1]["id"]]
        == candidate_2_discrepancy
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "discrepancies"
        ][choices[2]["id"]]
        == candidate_3_discrepancy
    )

    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "reportedVotes"
        ][choices[0]["id"]]
        == reported_tallies[choice_ids[0]]
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "reportedVotes"
        ][choices[1]["id"]]
        == reported_tallies[choice_ids[1]]
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "reportedVotes"
        ][choices[2]["id"]]
        == reported_tallies[choice_ids[2]]
    )

    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "auditedVotes"
        ][choices[0]["id"]]
        == reported_tallies[choice_ids[0]]
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "auditedVotes"
        ][choices[1]["id"]]
        == reported_tallies[choice_ids[1]] - candidate_2_discrepancy
    )
    assert (
        discrepancies[jurisdiction_ids[0]]["Combined Batch"][contests[0]["id"]][
            "auditedVotes"
        ][choices[2]["id"]]
        == reported_tallies[choice_ids[2]] - candidate_3_discrepancy
    )

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    expected_discrepancies = {
        "J1": {
            "Combined Batch": {
                "candidate 1": 0,
                "candidate 2": candidate_2_discrepancy,
                "candidate 3": candidate_3_discrepancy,
            },
        }
    }
    check_discrepancies(
        discrepancy_report, expected_discrepancies, contests[0]["choices"]
    )

    # Audit jurisdiction 2
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    j2_sampled_batches = json.loads(rv.data)["batches"]
    assert len(j2_sampled_batches) == 1

    # Audit the single sampled batch
    assert j2_sampled_batches[0]["name"] == "Batch 3"
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{j2_sampled_batches[0]['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": {
                    choice_ids[0]: 500,
                    choice_ids[1]: 250,
                    choice_ids[2]: 250,
                },
            }
        ],
    )
    assert_ok(rv)

    # Finalize the results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)


def test_batch_comparison_pending_ballots(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Get sample size options
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"][contest_id]
    assert len(sample_size_options) == 1

    # Check that pending ballots wasn't set by initial contest creation
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["pendingBallots"] is None

    # Add pending ballots to the target contest
    num_pending_ballots = 250
    del contest["totalBallotsCast"]
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [{**contest, "pendingBallots": num_pending_ballots}],
    )
    assert_ok(rv)

    # Check that pending ballots was set
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["pendingBallots"] == num_pending_ballots

    # Delete the cached sample size options
    SampleSizeOptions.query.filter_by(election_id=election_id, round_num=1).delete()
    db_session.commit()

    # Get sample size options again
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options_with_pending_ballots = json.loads(rv.data)["sampleSizes"][
        contest_id
    ]
    assert len(sample_size_options_with_pending_ballots) == 1

    # Confirm that the sample size increased, indicating that the pending
    # ballots were included in the sample size calculation
    assert (
        sample_size_options_with_pending_ballots[0]["size"]
        > sample_size_options[0]["size"]
    )
    snapshot.assert_match(sample_size_options_with_pending_ballots)

    # Launch the audit
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_id: sample_size_options_with_pending_ballots[0]},
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    # Audit all of the sampled batches correctly
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        batch_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
        )
        batches = json.loads(rv.data)["batches"]
        for batch in batches:
            tallies = batch_tallies[batch["name"]][contest_id]
            del tallies["ballots"]
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/{batch['id']}/results",
                [
                    {
                        "name": "Tally Sheet #1",
                        "results": tallies,
                    }
                ],
            )
            assert_ok(rv)

        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize",
        )
        assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    # Check the p-value against a p-value without pending ballots
    round = Round.query.get(round_1_id)
    assert len(round.round_contests) == 1
    round_contest = round.round_contests[0]
    p_value = round_contest.end_p_value

    # Hackily edit the contest to remove pending ballots
    Contest.query.filter_by(id=contest_id).update({"pending_ballots": 0})
    # Re-open the round
    round.ended_at = None
    round_contest.end_p_value = None
    round_contest.results = []
    round_contest.is_complete = False
    db_session.commit()
    # End the round again
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    # Check the p-value again
    round = Round.query.get(round_1_id)
    p_value_without_pending_ballots = round.round_contests[0].end_p_value

    # The p-value should be higher with pending ballots, proving that we did in
    # fact incorporate the pending ballots into the risk measurement
    # calculation, worst-casing them as votes for the loser. The actual
    # calculation correctness is tested in test_macro.py.
    assert p_value > p_value_without_pending_ballots


def test_batch_comparison_contests_pending_ballots_validation(
    client: FlaskClient,
    election_id: str,
    contest_id: str,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    del contest["totalBallotsCast"]

    invalid_pending_ballots = [
        "not a number",
        -1,
    ]
    for invalid_value in invalid_pending_ballots:
        rv = put_json(
            client,
            f"/api/election/{election_id}/contest",
            [{**contest, "pendingBallots": invalid_value}],
        )
        assert rv.status_code == 400
