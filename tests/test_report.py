import json

import pytest

from test_app import client, post_json, run_whole_audit_flow


def test_basic_report(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']
    assert election_id

    print("running whole audit flow " + election_id)
    run_whole_audit_flow(client, election_id, "Primary 2019", 10, "12345678901234567890")

    rv = client.get(f'/election/{election_id}/audit/report')
    lines = rv.data.decode('utf-8').splitlines()
    for line in EXPECTED_BASIC_REPORT:
        assert line in lines
    assert any(line.startswith("Round 1 Start,") for line in lines)
    assert any(line.startswith("Round 1 End,") for line in lines)
    assert any(line.startswith("Round 1 Samples,") for line in lines)
    assert len(lines) == len(EXPECTED_BASIC_REPORT) + 3


EXPECTED_BASIC_REPORT = [
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
    "Round 1 Audited Votes for candidate 1,579",
    "Round 1 Audited Votes for candidate 2,456",
    "Round 1 P-Value,0.000659152256587975",
    "Round 1 Risk Limit Met?,Yes",
    # Round 1 Start,2020-03-03 01:54:21.428260
    # Round 1 End,2020-03-03 01:54:23.316816
    # Round 1 Samples, ... a whole lotta stuff ...
]
