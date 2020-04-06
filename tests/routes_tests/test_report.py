import json, random
from flask.testing import FlaskClient

import pytest

from tests.helpers import post_json, create_election
from tests.test_app import setup_whole_audit, run_whole_audit_flow
import bgcompute


@pytest.fixture()
def election_id(client: FlaskClient) -> str:
    yield create_election(client, is_multi_jurisdiction=False)


def run_audit_round(
    client, audit_info, round_number, round_id, vote_ratio,
):
    (
        election_id,
        jurisdiction_id,
        contest_id,
        candidate_id_1,
        candidate_id_2,
    ) = audit_info

    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/ballot-list"
    )
    ballot_list = json.loads(rv.data)["ballots"]

    # "Audit" each ballot and post the vote
    rand = random.Random("12345678901234567890")
    for i, ballot in enumerate(ballot_list):
        vote = candidate_id_1 if rand.random() > vote_ratio else candidate_id_2
        if i == 2:
            vote = "Audit board can't agree"
        if i == 3:
            vote = "Blank vote/no mark"
        rv = post_json(
            client,
            f"/election/{election_id}/jurisdiction/{jurisdiction_id}/batch/{ballot['batch']['id']}/ballot/{ballot['position']}",
            {"vote": vote, "comment": f"Comment for ballot {i}" if i % 3 == 0 else "",},
        )
        assert json.loads(rv.data)["status"] == "ok"

    # The results won't be exact since we used a (seeded) random choice above.
    # If we need exact results, we can always query the db or track results above.
    num_for_winner = int(len(ballot_list) * vote_ratio)
    num_for_loser = len(ballot_list) - num_for_winner
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/{round_number}/results",
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser,
                    },
                }
            ]
        },
    )
    assert json.loads(rv.data)["status"] == "ok"

    return len(ballot_list)


def test_offline_audit_report(client, election_id):
    run_whole_audit_flow(
        client, election_id, "Primary 2019", 10, "12345678901234567890"
    )

    rv = client.get(f"/election/{election_id}/audit/report")
    lines = rv.data.decode("utf-8").splitlines()
    assert lines

    expected = [
        "Contest Name,contest 1",
        "Number of Winners,1",
        "Votes Allowed,1",
        "Total Ballots Cast,86147",
        "candidate 1 Votes,48121",
        "candidate 2 Votes,38026",
        "Risk Limit,10%",
        "Random Seed,12345678901234567890",
        "Round 1 Sample Size,1035",
        "Round 1 Audited Votes for candidate 2,456",
        "Round 1 Audited Votes for candidate 1,579",
        "Round 1 P-Value,0.000659152256587975",
        "Round 1 Risk Limit Met?,Yes",
        # Round 1 Start,2020-03-03 01:54:21.428260
        # Round 1 End,2020-03-03 01:54:23.316816
        # Round 1 Samples, ... a row containing all sampled ballots ...
    ]

    for line in expected:
        assert line in lines

    assert any(line.startswith("Round 1 Start,") for line in lines)
    assert any(line.startswith("Round 1 End,") for line in lines)
    assert any(line.startswith("Round 1 Samples,") for line in lines)

    assert len(lines) == len(expected) + 3


def test_one_round_audit_report(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890", online=True
    )
    audit_info = (
        election_id,
        jurisdiction_id,
        contest_id,
        candidate_id_1,
        candidate_id_2,
    )

    # Get the round id
    rv = client.get(f"/election/{election_id}/audit/status")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Run the first round such that the audit completes
    num_ballots = run_audit_round(client, audit_info, 1, round_1_id, 0.61,)

    # Check the report
    rv = client.get(f"/election/{election_id}/audit/report")
    lines = rv.data.decode("utf-8").splitlines()
    assert lines

    expected = [
        "Contest Name,contest 1",
        "Number of Winners,1",
        "Votes Allowed,1",
        "Total Ballots Cast,86147",
        "candidate 1 Votes,48121",
        "candidate 2 Votes,38026",
        "Risk Limit,10%",
        "Random Seed,12345678901234567890",
        "Audit Board #1,Joe Schmo,Republican",
        "Audit Board #1,Jane Plain,",
        "audit board #2,,",
        "audit board #2,,",
        "Round 1 Sample Size,1035",
        "Round 1 Audited Votes for candidate 1,631",
        "Round 1 Audited Votes for candidate 2,404",
        "Round 1 P-Value,3.17524869224731e-09",
        "Round 1 Risk Limit Met?,Yes",
        # Round 1 Start,2020-03-03 01:54:21.428260
        # Round 1 End,2020-03-03 01:54:23.316816
        # Round 1 Samples, ... a row containing all sampled ballots ...
        "All Sampled Ballots",
        "Ballot,Ticket Numbers,Audited?,Audit Result,Comments",
        # ... a row for every ballot ...
    ]

    for line in expected:
        assert line in lines

    assert any(line.startswith("Round 1 Start,") for line in lines)
    assert any(line.startswith("Round 1 End,") for line in lines)
    assert any(line.startswith("Round 1 Samples,") for line in lines)

    # We'll just test a sampling of lines that should include a good variety of cases
    ballot_lines = sorted(lines[lines.index("All Sampled Ballots") + 2 :])
    assert ballot_lines[:10] == [
        f'"Batch 1, #122",Round 1: 0.012066605,Audited,{candidate_id_1},',
        f'"Batch 10, #10",Round 1: 0.010939432,Audited,{candidate_id_1},Comment for ballot 0',
        '"Batch 10, #151",Round 1: 0.012381762,Audited,Blank vote/no mark,Comment for ballot 3',
        f'"Batch 10, #200",Round 1: 0.000030407,Audited,{candidate_id_2},',
        f'"Batch 10, #59",Round 1: 0.002728647,Audited,{candidate_id_1},',
        '"Batch 10, #72",Round 1: 0.009650515,Audited,Audit board can\'t agree,',
        f'"Batch 100, #149",Round 1: 0.005232785,Audited,{candidate_id_2},',
        f'"Batch 100, #15",Round 1: 0.011431396,Audited,{candidate_id_1},',
        f'"Batch 100, #21",Round 1: 0.008470690,Audited,{candidate_id_1},Comment for ballot 6',
        f'"Batch 100, #22",Round 1: 0.006770721,Audited,{candidate_id_1},',
    ]

    # Check one of the ballots sampled twice to ensure it formats correctly
    assert any(
        line.startswith('"Batch 404, #83","Round 1: 0.008146401, 0.010895077",Audited,')
        for line in ballot_lines
    )
    NUM_BALLOTS_SAMPLED_TWICE = 5  # Checked this by hand

    assert len(ballot_lines) == num_ballots - NUM_BALLOTS_SAMPLED_TWICE
    # We omitted out 3 non-deterministic lines from `expected`, so account for them here
    assert len(lines) == len(expected) + 3 + num_ballots - NUM_BALLOTS_SAMPLED_TWICE


def test_two_round_audit_report(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890", online=True
    )
    audit_info = (
        election_id,
        jurisdiction_id,
        contest_id,
        candidate_id_1,
        candidate_id_2,
    )

    # Get the first round id
    rv = client.get(f"/election/{election_id}/audit/status")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Run the first round such that the audit does not complete
    num_ballots = run_audit_round(client, audit_info, 1, round_1_id, 0.51)

    # Then run the second round such that the audit completes
    bgcompute.bgcompute()
    rv = client.get(f"/election/{election_id}/audit/status")
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]
    num_ballots += run_audit_round(client, audit_info, 2, round_2_id, 0.61)

    # Check the report
    rv = client.get(f"/election/{election_id}/audit/report")
    lines = rv.data.decode("utf-8").splitlines()
    assert lines

    expected = [
        "Contest Name,contest 1",
        "Number of Winners,1",
        "Votes Allowed,1",
        "Total Ballots Cast,86147",
        "candidate 1 Votes,48121",
        "candidate 2 Votes,38026",
        "Risk Limit,10%",
        "Random Seed,12345678901234567890",
        "Audit Board #1,Joe Schmo,Republican",
        "Audit Board #1,Jane Plain,",
        "audit board #2,,",
        "audit board #2,,",
        "Round 1 Sample Size,1035",
        "Round 1 Audited Votes for candidate 1,527",
        "Round 1 Audited Votes for candidate 2,508",
        "Round 1 P-Value,136.833911128237",
        "Round 1 Risk Limit Met?,No",
        # Round 1 Start,2020-03-03 01:54:21.428260
        # Round 1 End,2020-03-03 01:54:23.316816
        # Round 1 Samples, ... a row containing all sampled ballots ...
        "Round 2 Sample Size,2031",
        "Round 2 Audited Votes for candidate 1,1238",
        "Round 2 Audited Votes for candidate 2,793",
        "Round 2 P-Value,3.03944302625829e-15",
        "Round 2 Risk Limit Met?,Yes",
        # Round 2 Start,2020-03-03 01:54:21.428260
        # Round 2 End,2020-03-03 01:54:23.316816
        # Round 2 Samples, ... a row containing all sampled ballots ...
        "All Sampled Ballots",
        "Ballot,Ticket Numbers,Audited?,Audit Result,Comments",
        # ... a row for every ballot ...
    ]

    for line in expected:
        assert line in lines

    assert any(line.startswith("Round 1 Start,") for line in lines)
    assert any(line.startswith("Round 1 End,") for line in lines)
    assert any(line.startswith("Round 1 Samples,") for line in lines)
    assert any(line.startswith("Round 2 Start,") for line in lines)
    assert any(line.startswith("Round 2 End,") for line in lines)
    assert any(line.startswith("Round 2 Samples,") for line in lines)

    ballot_lines = sorted(lines[lines.index("All Sampled Ballots") + 2 :])

    # We'll just test a sampling of lines that should include a good variety of cases
    assert ballot_lines[:10] == [
        f'"Batch 1, #111",Round 2: 0.034167626,Audited,{candidate_id_1},Comment for ballot 0',
        f'"Batch 1, #122",Round 1: 0.012066605,Audited,{candidate_id_1},',
        f'"Batch 10, #10",Round 1: 0.010939432,Audited,{candidate_id_1},Comment for ballot 0',
        f'"Batch 10, #103",Round 2: 0.031357473,Audited,{candidate_id_1},',
        '"Batch 10, #151",Round 1: 0.012381762,Audited,Blank vote/no mark,Comment for ballot 3',
        '"Batch 10, #175",Round 2: 0.021956866,Audited,Audit board can\'t agree,',
        f'"Batch 10, #200",Round 1: 0.000030407,Audited,{candidate_id_2},',
        f'"Batch 10, #59",Round 1: 0.002728647,Audited,{candidate_id_1},',
        '"Batch 10, #72",Round 1: 0.009650515,Audited,Audit board can\'t agree,',
        '"Batch 100, #106",Round 2: 0.015314474,Audited,Blank vote/no mark,Comment for ballot 3',
    ]

    # Check one of the ballots sampled in both rounds to make sure it formats correctly
    assert any(
        line.startswith(
            '"Batch 257, #162","Round 1: 0.012445813, Round 2: 0.020121449",Audited,'
        )
        for line in ballot_lines
    )

    # Ballots sampled twice in one round + ballots sampled in both rounds
    NUM_BALLOTS_SAMPLED_TWICE = 26 + 20  # Checked this by hand
    assert len(ballot_lines) == num_ballots - NUM_BALLOTS_SAMPLED_TWICE
    # We omitted out 6 non-deterministic lines from `expected`, so account for them here
    assert len(lines) == len(expected) + 6 + num_ballots - NUM_BALLOTS_SAMPLED_TWICE
