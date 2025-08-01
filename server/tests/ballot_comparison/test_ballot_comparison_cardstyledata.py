import io
import json
import csv
from flask.testing import FlaskClient
import pytest

from server.tests.ballot_comparison.test_ballot_comparison import (
    audit_all_ballots,
    check_discrepancies,
)

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .conftest import (
    TEST_CVRS,
)


@pytest.mark.parametrize(
    "election_id",
    [{"audit_math_type": AuditMathType.CARDSTYLEDATA}],
    indirect=True,
)
def test_ballot_comparison_cardstyledata_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    # AA uploads standardized contests file
    rv = upload_standardized_contests(
        client,
        io.BytesIO(
            b"Contest Name,Jurisdictions\n"
            b'Contest 1,"J1,J2"\n'
            b'Contest 2,"J1,J2"\n'
            b"Contest 3,J2\n"
        ),
        election_id,
    )
    assert_ok(rv)

    # AA selects a contest to target from the standardized contest list
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    standardized_contests = json.loads(rv.data)

    target_contest = standardized_contests[0]
    opportunistic_contest = standardized_contests[1]
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": target_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": target_contest["jurisdictionIds"],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": opportunistic_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": opportunistic_contest["jurisdictionIds"],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # JA uploads CVRs
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_cvrs(
        client,
        io.BytesIO(TEST_CVRS.encode()),
        election_id,
        jurisdiction_ids[0],
        "DOMINION",
    )
    assert_ok(rv)
    rv = upload_cvrs(
        client,
        io.BytesIO(TEST_CVRS.encode()),
        election_id,
        jurisdiction_ids[1],
        "DOMINION",
    )
    assert_ok(rv)

    # Validate the totalBallotsCast for each contest is only the ballots with the contest,
    # not the total ballots cast in the election.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    print("Contest data:", json.loads(rv.data))
    target_contest = json.loads(rv.data)["contests"][0]
    assert target_contest["totalBallotsCast"] == 22
    opportunistic_contest = json.loads(rv.data)["contests"][1]
    assert opportunistic_contest["totalBallotsCast"] == 28

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]
    opportunistic_contest_id = contests[1]["id"]

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]
    snapshot.assert_match(sample_size)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Check jurisdiction status after starting the round
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Audit boards audit all the ballots.
    # Our goal is to mostly make the audit board interpretations match the CVRs
    # for the target contest, messing up just a couple in order to trigger a
    # second round. For convenience, using the same format as the CVR to
    # specify our audit results.
    # Tabulator, Batch, Ballot, Choice 1-1, Choice 1-2, Choice 2-1, Choice 2-2, Choice 2-3
    # We also specify the expected discrepancies.
    round_1_audit_results_j1 = {
        ("J1", "TABULATOR1", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 2): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 3): ("1,1,0,1,1", (1, 2)),  # CVR: 1,0,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
    }

    round_1_audit_results_j2 = {
        ("J2", "TABULATOR1", "BATCH1", 1): ("1,0,1,0,0", (-2, -1)),  # CVR: 0,1,1,1,0
        ("J2", "TABULATOR1", "BATCH1", 2): ("0,0,0,0,0", (1, 1)),  # CVR: 1,0,1,0,1
        ("J2", "TABULATOR1", "BATCH1", 3): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 1): ("1,0,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
    }
    round_1_audit_results = {**round_1_audit_results_j1, **round_1_audit_results_j2}

    audit_all_ballots(
        round_1_id,
        round_1_audit_results,
        target_contest_id,
        opportunistic_contest_id,
    )

    # Only sign off J1
    audit_boards = AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_ids[0]).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing J1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "IN_PROGRESS"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check discrepancies
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    target_contest_discrepancies = discrepancies[jurisdictions[0]["id"]][
        "TABULATOR1, BATCH2, Ballot 3"
    ][target_contest_id]
    contest_choices = contests[0]["choices"]
    assert target_contest_discrepancies["auditedVotes"][contest_choices[0]["id"]] == "1"
    assert (
        target_contest_discrepancies["reportedVotes"][contest_choices[0]["id"]] == "1"
    )
    assert target_contest_discrepancies["discrepancies"][contest_choices[0]["id"]] == 0
    assert target_contest_discrepancies["auditedVotes"][contest_choices[1]["id"]] == "1"
    assert (
        target_contest_discrepancies["reportedVotes"][contest_choices[1]["id"]] == "0"
    )
    assert target_contest_discrepancies["discrepancies"][contest_choices[1]["id"]] == -1

    opportunistic_contest_discrepancies = discrepancies[jurisdictions[0]["id"]][
        "TABULATOR1, BATCH2, Ballot 3"
    ][opportunistic_contest_id]
    contest_choices = contests[1]["choices"]
    assert (
        opportunistic_contest_discrepancies["auditedVotes"][contest_choices[0]["id"]]
        == "0"
    )
    assert (
        opportunistic_contest_discrepancies["reportedVotes"][contest_choices[0]["id"]]
        == "1"
    )
    assert (
        opportunistic_contest_discrepancies["discrepancies"][contest_choices[0]["id"]]
        == 1
    )
    assert (
        opportunistic_contest_discrepancies["auditedVotes"][contest_choices[1]["id"]]
        == "1"
    )
    assert (
        opportunistic_contest_discrepancies["reportedVotes"][contest_choices[1]["id"]]
        == "0"
    )
    assert (
        opportunistic_contest_discrepancies["discrepancies"][contest_choices[1]["id"]]
        == -1
    )

    # Discrepancies should not show before the audit board is signed off, check J2
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert jurisdictions[1]["id"] not in discrepancies

    # Also check the discrepancy report - only the first jurisdiction should have
    # audit results so far since the second jurisdiction hasn't signed off yet
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    check_discrepancies(discrepancy_report, round_1_audit_results_j1)
    for row in csv.DictReader(io.StringIO(discrepancy_report)):
        if row["Jurisdiction Name"] == "J2":
            assert row["Audited?"] == "NOT_AUDITED"
            assert row["Audit Result: Contest 1"] == ""
            assert row["CVR Result: Contest 1"] == ""
            assert row["Change in Results: Contest 1"] == ""
            assert row["Change in Margin: Contest 1"] == ""

    # Sign off J2
    audit_boards = AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_ids[1]).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing J2
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "COMPLETE"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Discrepancies should now show for J2
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert jurisdictions[1]["id"] in discrepancies

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    )
    check_discrepancies(discrepancy_report, round_1_audit_results)

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

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # Sample sizes endpoint should still return round 1 sample size
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    assert sample_size_options[target_contest_id][0] == sample_size

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_2_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # For round 2, audit results should not have any positive discrepancies so
    # the audit can complete.
    round_2_audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
    }

    audit_all_ballots(
        round_2_id, round_2_audit_results, target_contest_id, opportunistic_contest_id
    )
    audit_boards = AuditBoard.query.filter(
        AuditBoard.jurisdiction_id.in_(jurisdiction_ids)
    ).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "COMPLETE"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the discrepancies
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    assert len(discrepancies) == 1

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    )
    check_discrepancies(discrepancy_report, round_2_audit_results)
