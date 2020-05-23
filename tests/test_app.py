import os, math, uuid
import json, csv, io
from flask.testing import FlaskClient
import pytest

from tests.helpers import assert_ok, post_json, create_election
import bgcompute

manifest_file_path = os.path.join(os.path.dirname(__file__), "manifest.csv")
small_manifest_file_path = os.path.join(os.path.dirname(__file__), "small-manifest.csv")


@pytest.fixture()
def election_id(client: FlaskClient) -> str:
    return create_election(client, is_multi_jurisdiction=False)


def test_index(client):
    rv = client.get("/")
    assert b"Arlo (by VotingWorks)" in rv.data

    rv = client.get("/election/1234")
    assert b"Arlo (by VotingWorks)" in rv.data

    rv = client.get("/election/1234/audit-board/5677")
    assert b"Arlo (by VotingWorks)" in rv.data


def test_static_logo(client):
    rv = client.get("/arlo.png")
    assert rv.status_code == 200


def test_session(client):
    rv = client.get("/incr")
    assert json.loads(rv.data) == {"count": 1}

    rv = client.get("/incr")
    assert json.loads(rv.data) == {"count": 2}


def test_whole_audit_flow(client: FlaskClient):
    election_id_1 = create_election(
        client, audit_name="Audit 1", is_multi_jurisdiction=False
    )
    election_id_2 = create_election(
        client, audit_name="Audit 2", is_multi_jurisdiction=False
    )

    print("running whole audit flow " + election_id_1)
    run_whole_audit_flow(
        client, election_id_1, "Primary 2019", 10, "12345678901234567890"
    )

    print("running whole audit flow " + election_id_2)
    run_whole_audit_flow(
        client, election_id_2, "General 2019", 5, "12345678901234599999"
    )

    # after resetting election 1, election 2 is still around
    run_election_reset(client, election_id_1)

    rv = client.get("/election/{}/audit/status".format(election_id_2))
    result2 = json.loads(rv.data)
    assert result2["riskLimit"] == 5


def setup_audit_board(client, election_id, jurisdiction_id, audit_board_id):
    rv = post_json(
        client,
        "/election/{}/jurisdiction/{}/audit-board/{}".format(
            election_id, jurisdiction_id, audit_board_id
        ),
        {
            "name": "Audit Board #1",
            "members": [
                {"name": "Joe Schmo", "affiliation": "REP"},
                {"name": "Jane Plain", "affiliation": ""},
            ],
        },
    )

    assert_ok(rv)


def setup_whole_audit(client, election_id, name, risk_limit, random_seed, online=False):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    url_prefix = "/election/{}".format(election_id)

    rv = post_json(
        client,
        "{}/audit/basic".format(url_prefix),
        {
            "name": name,
            "riskLimit": risk_limit,
            "randomSeed": random_seed,
            "online": online,
            "contests": [
                {
                    "id": contest_id,
                    "name": "contest 1",
                    "isTargeted": True,
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "candidate 1",
                            "numVotes": 48121,
                        },
                        {
                            "id": candidate_id_2,
                            "name": "candidate 2",
                            "numVotes": 38026,
                        },
                    ],
                    "totalBallotsCast": 86147,
                    "numWinners": 1,
                    "votesAllowed": 1,
                }
            ],
        },
    )

    assert_ok(rv)

    rv = client.post(f"{url_prefix}/audit/freeze")
    assert_ok(rv)

    # before background compute, should be null sample size options
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    assert status["rounds"][0]["contests"][0]["sampleSizeOptions"] is None
    assert status["online"] == online

    # after background compute
    bgcompute.bgcompute()
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    assert len(status["rounds"][0]["contests"][0]["sampleSizeOptions"]) == 4

    assert status["randomSeed"] == random_seed
    assert len(status["contests"]) == 1
    assert status["riskLimit"] == risk_limit
    assert status["name"] == name

    assert status["contests"][0]["choices"][0]["id"] == candidate_id_1

    rv = post_json(
        client,
        "{}/audit/jurisdictions".format(url_prefix),
        {
            "jurisdictions": [
                {
                    "id": jurisdiction_id,
                    "name": "adams county",
                    "contests": [contest_id],
                    "auditBoards": [
                        {
                            "id": audit_board_id_1,
                            "name": "audit board #1",
                            "members": [],
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "audit board #2",
                            "members": [],
                        },
                    ],
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "adams county"
    assert jurisdiction["auditBoards"][1]["name"] == "audit board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_90 = [
        option
        for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"]
        if option["prob"] == 0.9
    ]
    assert len(sample_size_90) == 1
    sample_size = sample_size_90[0]["size"]

    # set the sample_size
    rv = post_json(
        client, "{}/audit/sample-size".format(url_prefix), {"size": sample_size}
    )

    assert_ok(rv)

    # upload the manifest
    data = {}
    data["manifest"] = (open(manifest_file_path, "rb"), "manifest.csv")
    rv = client.put(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id),
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 86147
    assert manifest["numBatches"] == 484
    assert manifest["file"]["name"] == "manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # delete the manifest and make sure that works
    rv = client.delete(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id)
    )
    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["file"] is None

    # upload the manifest again
    data = {}
    data["manifest"] = (open(manifest_file_path, "rb"), "manifest.csv")
    rv = client.put(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id),
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    setup_audit_board(client, election_id, jurisdiction_id, audit_board_id_1)

    # get the retrieval list for round 1
    rv = client.get(
        "{}/jurisdiction/{}/1/retrieval-list".format(url_prefix, jurisdiction_id)
    )
    lines = rv.data.decode("utf-8").splitlines()
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    )
    assert len(lines) > 5
    assert "attachment" in rv.headers["content-disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    return (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    )


def setup_whole_multi_winner_audit(client, election_id, name, risk_limit, random_seed):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    candidate_id_3 = str(uuid.uuid4())
    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    url_prefix = "/election/{}".format(election_id)

    rv = post_json(
        client,
        "{}/audit/basic".format(url_prefix),
        {
            "name": name,
            "riskLimit": risk_limit,
            "randomSeed": random_seed,
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "contest 1",
                    "isTargeted": True,
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "candidate 1",
                            "numVotes": 43121,
                        },
                        {
                            "id": candidate_id_2,
                            "name": "candidate 2",
                            "numVotes": 38026,
                        },
                        {"id": candidate_id_3, "name": "candidate 3", "numVotes": 5000},
                    ],
                    "totalBallotsCast": 86147,
                    "numWinners": 2,
                    "votesAllowed": 1,
                }
            ],
        },
    )

    assert_ok(rv)

    rv = client.post(f"{url_prefix}/audit/freeze")
    assert_ok(rv)

    # before background compute, should be null sample size options
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    assert status["rounds"][0]["contests"][0]["sampleSizeOptions"] is None

    # after background compute
    bgcompute.bgcompute()
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    # We should only get the expected sample size for multi-winner
    assert len(status["rounds"][0]["contests"][0]["sampleSizeOptions"]) == 1

    assert status["randomSeed"] == random_seed
    assert len(status["contests"]) == 1
    assert status["riskLimit"] == risk_limit
    assert status["name"] == name

    assert status["contests"][0]["choices"][0]["id"] == candidate_id_1

    rv = post_json(
        client,
        "{}/audit/jurisdictions".format(url_prefix),
        {
            "jurisdictions": [
                {
                    "id": jurisdiction_id,
                    "name": "adams county",
                    "contests": [contest_id],
                    "auditBoards": [
                        {
                            "id": audit_board_id_1,
                            "name": "audit board #1",
                            "members": [],
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "audit board #2",
                            "members": [],
                        },
                    ],
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "adams county"
    assert jurisdiction["auditBoards"][1]["name"] == "audit board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_asn = status["rounds"][0]["contests"][0]["sampleSizeOptions"]
    assert len(sample_size_asn) == 1
    sample_size = sample_size_asn[0]["size"]

    # set the sample_size
    rv = post_json(
        client, "{}/audit/sample-size".format(url_prefix), {"size": sample_size}
    )

    assert_ok(rv)

    # upload the manifest
    data = {}
    data["manifest"] = (open(manifest_file_path, "rb"), "manifest.csv")
    rv = client.put(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id),
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 86147
    assert manifest["numBatches"] == 484
    assert manifest["file"]["name"] == "manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # delete the manifest and make sure that works
    rv = client.delete(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id)
    )
    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["file"] is None

    # upload the manifest again
    data = {}
    data["manifest"] = (open(manifest_file_path, "rb"), "manifest.csv")
    rv = client.put(
        "{}/jurisdiction/{}/manifest".format(url_prefix, jurisdiction_id),
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    # get the retrieval list for round 1
    rv = client.get(
        "{}/jurisdiction/{}/1/retrieval-list".format(url_prefix, jurisdiction_id)
    )
    lines = rv.data.decode("utf-8").split("\r\n")
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    )
    assert len(lines) > 5
    assert "attachment" in rv.headers["content-disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    return (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        candidate_id_3,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    )


def run_whole_audit_flow(client, election_id, name, risk_limit, random_seed):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        _audit_board_id_1,
        _audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(client, election_id, name, risk_limit, random_seed)

    # post results for round 1
    num_for_winner = int(num_ballots * 0.56)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        "{}/jurisdiction/{}/1/results".format(url_prefix, jurisdiction_id),
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

    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 5


def run_election_reset(client, election_id):
    url_prefix = "/election/{}".format(election_id)

    # reset
    rv = client.post("{}/audit/reset".format(url_prefix))
    response = json.loads(rv.data)
    assert response["status"] == "ok"

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)

    assert status["riskLimit"] is None
    assert status["randomSeed"] is None
    assert status["contests"] == []
    assert status["jurisdictions"] == []
    assert status["rounds"] == []


def get_lines_from_retrieval_list(rv):
    return list(csv.DictReader(io.StringIO(rv.data.decode("utf-8"))))


def get_num_ballots_from_retrieval_list(rv):
    lines = get_lines_from_retrieval_list(rv)

    for line in lines:
        print(line)
    return sum([len(line["Ticket Numbers"].split(",")) for line in lines])


def test_small_election(client, election_id):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/election/{election_id}/audit/basic",
        {
            "name": "Small Test 2019",
            "riskLimit": 10,
            "randomSeed": "a1234567890987654321b",
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "choices": [
                        {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 1325},
                        {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 792},
                    ],
                    "totalBallotsCast": 2123,
                    "numWinners": 1,
                    "votesAllowed": 1,
                }
            ],
        },
    )

    assert_ok(rv)

    # not yet frozen
    rv = client.get(f"/election/{election_id}/audit/status")
    assert not json.loads(rv.data)["frozenAt"]

    rv = client.post(f"/election/{election_id}/audit/freeze")
    assert_ok(rv)

    # now frozen
    rv = client.get(f"/election/{election_id}/audit/status")
    frozen_at = json.loads(rv.data)["frozenAt"]
    assert frozen_at

    # make sure freezing twice doesn't change frozen date
    rv = client.post(f"/election/{election_id}/audit/freeze")
    rv = client.get(f"/election/{election_id}/audit/status")
    frozen_at_2 = json.loads(rv.data)["frozenAt"]

    assert frozen_at == frozen_at_2

    bgcompute.bgcompute()

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["name"] == "Small Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/election/{election_id}/audit/jurisdictions",
        {
            "jurisdictions": [
                {
                    "id": jurisdiction_id,
                    "name": "County 1",
                    "contests": [contest_id],
                    "auditBoards": [
                        {
                            "id": audit_board_id_1,
                            "name": "Audit Board #1",
                            "members": [],
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "Audit Board #2",
                            "members": [],
                        },
                    ],
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "County 1"
    assert jurisdiction["auditBoards"][1]["name"] == "Audit Board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_90 = [
        option
        for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"]
        if option["prob"] == 0.9
    ]
    assert len(sample_size_90) == 1
    sample_size = sample_size_90[0]["size"]

    # set the sample_size
    rv = post_json(
        client, f"/election/{election_id}/audit/sample-size", {"size": sample_size}
    )

    # upload the manifest
    data = {}
    data["manifest"] = (open(small_manifest_file_path, "rb"), "small-manifest.csv")
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest",
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 2117
    assert manifest["numBatches"] == 10
    assert manifest["file"]["name"] == "small-manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # get the retrieval list for round 1
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list"
    )

    # deterministic sampling, should be the same every time, tweak for CRLF
    assert rv.data.decode("utf-8").replace("\r\n", "\n") == EXPECTED_RETRIEVAL_LIST

    lines = rv.data.decode("utf-8").splitlines()
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    )
    assert "attachment" in rv.headers["Content-Disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results",
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

    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f"/election/{election_id}/report")
    lines = rv.data.decode("utf-8").splitlines()
    assert lines[0] == "######## ELECTION INFO ########"
    assert "attachment" in rv.headers["Content-Disposition"]


def test_contest_choices_cannot_have_more_votes_than_allowed(client, election_id):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    # bad request, 21 + 40 actual votes > 30 * 2 allowed votes
    rv = post_json(
        client,
        f"/election/{election_id}/audit/basic",
        {
            "name": "Small Test 2019",
            "riskLimit": 10,
            "randomSeed": "a1234567890987654321b",
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "choices": [
                        {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 21},
                        {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 40},
                    ],
                    "totalBallotsCast": 30,
                    "numWinners": 1,
                    "votesAllowed": 2,
                }
            ],
        },
    )

    response = json.loads(rv.data)
    assert response == {
        "errors": [
            {
                "message": "Too many votes cast in contest: Contest 1 (61 votes, 60 allowed)",
                "errorType": "TooManyVotes",
            }
        ]
    }

    # good request, 20 + 40 actual votes <= 30 * 2 allowed votes
    rv = post_json(
        client,
        f"/election/{election_id}/audit/basic",
        {
            "name": "Small Test 2019",
            "riskLimit": 10,
            "randomSeed": "a1234567890987654321b",
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "choices": [
                        {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 20},
                        {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 40},
                    ],
                    "totalBallotsCast": 30,
                    "numWinners": 1,
                    "votesAllowed": 2,
                }
            ],
        },
    )

    response = json.loads(rv.data)
    assert response == {"status": "ok"}


def test_multi_round_audit(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        _audit_board_id_1,
        _audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Multi-Round Audit", 10, "32423432423432"
    )

    # post results for round 1 with 50/50 split, should not complete.
    num_for_winner = int(num_ballots * 0.5)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        "{}/jurisdiction/{}/1/results".format(url_prefix, jurisdiction_id),
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

    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_loser

    # should be incomplete
    assert not round_contest["endMeasurements"]["isComplete"]

    # next round is just set up
    assert len(status["rounds"]) == 2
    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"] is None

    # sample size
    bgcompute.bgcompute()
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)

    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"]
    assert status["rounds"][1]["contests"][0]["sampleSize"]

    # round 2 retrieval list should be ready
    rv = client.get(
        "{}/jurisdiction/{}/2/retrieval-list".format(url_prefix, jurisdiction_id)
    )

    # Count the ticket numbers
    num_ballots = get_num_ballots_from_retrieval_list(rv)
    assert num_ballots == status["rounds"][1]["contests"][0]["sampleSize"]

    # Check the already-retrieved
    lines = get_lines_from_retrieval_list(rv)
    already_audited = [
        (l["Batch Name"], l["Ballot Number"])
        for l in lines
        if l["Already Audited"] == "Y"
    ]
    assert already_audited == EXPECTED_ALREADY_AUDITED_BALLOTS


def test_multi_winner_election(client, election_id):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    candidate_id_3 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/election/{election_id}/audit/basic",
        {
            "name": "Small Multi-winner Test 2019",
            "riskLimit": 10,
            "randomSeed": "a1234567890987654321b",
            "online": False,
            "contests": [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "isTargeted": True,
                    "choices": [
                        {"id": candidate_id_1, "name": "Candidate 1", "numVotes": 1000},
                        {"id": candidate_id_2, "name": "Candidate 2", "numVotes": 792},
                        {"id": candidate_id_3, "name": "Candidate 3", "numVotes": 331},
                    ],
                    "totalBallotsCast": 2123,
                    "numWinners": 2,
                    "votesAllowed": 1,
                }
            ],
        },
    )

    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["name"] == "Small Multi-winner Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/election/{election_id}/audit/jurisdictions",
        {
            "jurisdictions": [
                {
                    "id": jurisdiction_id,
                    "name": "County 1",
                    "contests": [contest_id],
                    "auditBoards": [
                        {
                            "id": audit_board_id_1,
                            "name": "Audit Board #1",
                            "members": [],
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "Audit Board #2",
                            "members": [],
                        },
                    ],
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.post(f"/election/{election_id}/audit/freeze")
    assert_ok(rv)
    bgcompute.bgcompute()

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "County 1"
    assert jurisdiction["auditBoards"][1]["name"] == "Audit Board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_asn = status["rounds"][0]["contests"][0]["sampleSizeOptions"]
    assert len(sample_size_asn) == 1
    sample_size = sample_size_asn[0]["size"]

    # set the sample_size
    rv = post_json(
        client, f"/election/{election_id}/audit/sample-size", {"size": sample_size}
    )

    # upload the manifest
    data = {}
    data["manifest"] = (open(small_manifest_file_path, "rb"), "small-manifest.csv")
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest",
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    assert bgcompute.bgcompute_update_ballot_manifest_file() == 1

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 2117
    assert manifest["numBatches"] == 10
    assert manifest["file"]["name"] == "small-manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # get the retrieval list for round 1
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list"
    )
    lines = rv.data.decode("utf-8").split("\r\n")
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    )
    assert "attachment" in rv.headers["Content-Disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_winner2 = int(num_ballots * 0.3)
    num_for_loser = num_ballots - num_for_winner - num_for_winner2
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results",
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_winner2,
                        candidate_id_3: num_for_loser,
                    },
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_winner2
    assert round_contest["results"][candidate_id_3] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f"/election/{election_id}/report")
    lines = rv.data.decode("utf-8").splitlines()
    assert lines[0] == "######## ELECTION INFO ########"
    assert "attachment" in rv.headers["Content-Disposition"]


def test_multi_round_multi_winner_audit(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        candidate_id_3,
        jurisdiction_id,
        _audit_board_id_1,
        _audit_board_id_2,
        num_ballots,
    ) = setup_whole_multi_winner_audit(
        client, election_id, "Multi-Round Multi-winner Audit", 10, "32423432423432"
    )

    # post results for round 1 with 50/50 split, should not complete.
    num_for_winner = int(num_ballots * 0.4)
    num_for_winner2 = int(num_ballots * 0.4)
    num_for_loser = num_ballots - num_for_winner - num_for_winner2
    rv = post_json(
        client,
        "{}/jurisdiction/{}/1/results".format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_winner2,
                        candidate_id_3: num_for_loser,
                    },
                }
            ]
        },
    )

    assert_ok(rv)

    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_winner2
    assert round_contest["results"][candidate_id_3] == num_for_loser

    # should be incomplete
    assert not round_contest["endMeasurements"]["isComplete"]

    # next round is just set up
    assert len(status["rounds"]) == 2
    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"] is None

    # sample size
    bgcompute.bgcompute()
    rv = client.get("{}/audit/status".format(url_prefix))
    status = json.loads(rv.data)

    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"]
    assert status["rounds"][1]["contests"][0]["sampleSize"]

    # round 2 retrieval list should be ready
    rv = client.get(
        "{}/jurisdiction/{}/2/retrieval-list".format(url_prefix, jurisdiction_id)
    )
    num_ballots = get_num_ballots_from_retrieval_list(rv)
    assert num_ballots == status["rounds"][1]["contests"][0]["sampleSize"]


def test_ballot_set(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        _candidate_id_2,
        _candidate_id_3,
        jurisdiction_id,
        _audit_board_id_1,
        _audit_board_id_2,
        _num_ballots,
    ) = setup_whole_multi_winner_audit(
        client, election_id, "Multi-Round Multi-winner Audit", 10, "32423432423432"
    )

    ## find a sampled ballot to update
    rv = client.get("{}/audit/status".format(url_prefix))
    response = json.loads(rv.data)
    rounds = response["rounds"]
    batch_id = None
    round_id = None
    ballot = None

    for round in rounds:
        rv = client.get(
            "{}/jurisdiction/{}/round/{}/ballot-list".format(
                url_prefix, jurisdiction_id, round["id"]
            )
        )
        response = json.loads(rv.data)

        if response["ballots"]:
            ballot = response["ballots"][0]
            batch_id = ballot["batch"]["id"]
            round_id = round["id"]
            assert ballot["status"] == "NOT_AUDITED"
            assert ballot["interpretations"] == []
            break

    assert batch_id is not None
    assert round_id is not None
    assert ballot is not None

    ## set the ballot data
    url = "{}/jurisdiction/{}/batch/{}/ballot/{}".format(
        url_prefix, jurisdiction_id, batch_id, ballot["position"]
    )

    rv = post_json(
        client,
        url,
        {
            "interpretations": [
                {
                    "contestId": contest_id,
                    "interpretation": "VOTE",
                    "choiceId": candidate_id_1,
                    "comment": "This one had a hanging chad.",
                }
            ]
        },
    )
    response = json.loads(rv.data)

    assert response["status"] == "ok"

    ## verify the update actually did something
    rv = client.get(
        "{}/jurisdiction/{}/round/{}/ballot-list".format(
            url_prefix, jurisdiction_id, round_id
        )
    )
    response = json.loads(rv.data)
    ballot_position = ballot["position"]
    ballot = [b for b in response["ballots"] if b["position"] == ballot_position][0]

    assert ballot["status"] == "AUDITED"
    assert ballot["interpretations"] == [
        {
            "contestId": contest_id,
            "interpretation": "VOTE",
            "choiceId": candidate_id_1,
            "comment": "This one had a hanging chad.",
        }
    ]

    ## mark the ballot not found
    rv = client.post(
        f"{url_prefix}/jurisdiction/{jurisdiction_id}/batch/{batch_id}/ballot/{ballot_position}/set-not-found"
    )

    response = json.loads(rv.data)
    assert response["status"] == "ok"

    ## verify the update actually did something
    rv = client.get(
        "{}/jurisdiction/{}/round/{}/ballot-list".format(
            url_prefix, jurisdiction_id, round_id
        )
    )
    response = json.loads(rv.data)
    ballot = [b for b in response["ballots"] if b["position"] == ballot_position][0]

    assert ballot["status"] == "NOT_FOUND"
    assert ballot["interpretations"] == []


def test_audit_board(client, election_id):
    (
        url_prefix,
        _contest_id,
        _candidate_id_1,
        _candidate_id_2,
        _candidate_id_3,
        jurisdiction_id,
        audit_board_id_1,
        _audit_board_id_2,
        _num_ballots,
    ) = setup_whole_multi_winner_audit(
        client, election_id, "Multi-Round Multi-winner Audit", 10, "32423432423432"
    )
    url = "{}/jurisdiction/{}/audit-board/{}".format(
        url_prefix, jurisdiction_id, audit_board_id_1
    )

    ## check audit board
    rv = client.get(url)
    response = json.loads(rv.data)

    assert response["id"] == audit_board_id_1
    assert response["name"]
    assert response["members"] == []

    ## submit new data
    rv = post_json(
        client,
        url,
        {
            "name": "Awesome Audit Board",
            "members": [
                {"name": "Darth Vader", "affiliation": "EMP"},
                {"name": "Leia Organa", "affiliation": "REB"},
            ],
        },
    )
    response = json.loads(rv.data)

    assert response["status"] == "ok"

    ## check new data
    rv = client.get(url)
    response = json.loads(rv.data)

    assert response["id"] == audit_board_id_1
    assert response["name"] == "Awesome Audit Board"
    assert response["members"] == [
        {"name": "Darth Vader", "affiliation": "EMP"},
        {"name": "Leia Organa", "affiliation": "REB"},
    ]


EXPECTED_ALREADY_AUDITED_BALLOTS = [
    ("112", "146"),
    ("136", "118"),
    ("240", "174"),
    ("327", "85"),
    ("341", "52"),
    ("434", "101"),
    ("71", "46"),
    ("145", "134"),
    ("146", "152"),
    ("189", "26"),
    ("197", "150"),
    ("22", "103"),
    ("222", "4"),
    ("227", "147"),
    ("271", "6"),
    ("275", "162"),
    ("281", "30"),
    ("31", "13"),
    ("323", "175"),
    ("354", "182"),
    ("446", "59"),
    ("46", "44"),
    ("483", "13"),
    ("60", "11"),
]

EXPECTED_RETRIEVAL_LIST = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
2,1,,,0.051285890415970559,N,Audit Board #1
2,12,,,0.039500694424306965,N,Audit Board #1
2,15,,,0.022297876639307526,N,Audit Board #1
2,33,,,0.083437628942067010,N,Audit Board #1
2,37,,,0.049404132325491493,N,Audit Board #1
2,77,,,0.011444765072416337,N,Audit Board #1
2,78,,,0.065235158719060320,N,Audit Board #1
2,93,,,0.085982349406725821,N,Audit Board #1
2,107,,,"0.055192852686570875,0.062597461043650666",N,Audit Board #1
2,117,,,0.079468520906666102,N,Audit Board #1
2,123,,,0.026064338408750868,N,Audit Board #1
2,124,,,0.009739290103348502,N,Audit Board #1
2,136,,,0.061799951547976190,N,Audit Board #1
2,144,,,0.091785694830960939,N,Audit Board #1
2,182,,,0.074618452441383338,N,Audit Board #1
2,194,,,"0.047151231632088708,0.075256824516444292",N,Audit Board #1
2,199,,,0.026376966864967831,N,Audit Board #1
2,209,,,0.080512568006320329,N,Audit Board #1
2,224,,,0.067184755773052898,N,Audit Board #1
2,226,,,0.045082075967750041,N,Audit Board #1
2,232,,,0.070914470844790166,N,Audit Board #1
2,261,,,0.076081179993988525,N,Audit Board #1
2,263,,,0.060659269929563478,N,Audit Board #1
3,4,,,0.061537690996662214,N,Audit Board #1
3,31,,,0.029862723925803684,N,Audit Board #1
3,33,,,0.063033033371807185,N,Audit Board #1
3,35,,,0.088031358156943863,N,Audit Board #1
3,44,,,0.062288103661448716,N,Audit Board #1
3,47,,,0.027294463742458204,N,Audit Board #1
3,59,,,0.001909776885144933,N,Audit Board #1
3,80,,,0.087253393337473782,N,Audit Board #1
3,85,,,0.048683168456161924,N,Audit Board #1
3,88,,,"0.028211968896418007,0.031651590902487624",N,Audit Board #1
3,93,,,0.048579436222513842,N,Audit Board #1
3,117,,,0.065532510520489817,N,Audit Board #1
3,139,,,0.051692007333723531,N,Audit Board #1
3,154,,,0.066155011891551603,N,Audit Board #1
3,167,,,0.065394512537061287,N,Audit Board #1
3,171,,,0.042219491445984190,N,Audit Board #1
3,176,,,"0.005218780228956377,0.062366878262150498",N,Audit Board #1
4,2,,,0.076443972342575130,N,Audit Board #1
4,17,,,0.053430602429615010,N,Audit Board #1
4,23,,,0.058163275554481837,N,Audit Board #1
4,24,,,0.016410407413399229,N,Audit Board #1
4,25,,,0.045120258267664323,N,Audit Board #1
4,37,,,0.007555011788532484,N,Audit Board #1
4,54,,,0.010756792711184469,N,Audit Board #1
4,92,,,0.084574975017724608,N,Audit Board #1
4,95,,,0.016333584301022767,N,Audit Board #1
4,113,,,0.019848217156181455,N,Audit Board #1
4,129,,,0.080770854212536612,N,Audit Board #1
4,140,,,0.037883280576929254,N,Audit Board #1
4,143,,,0.084166260118524988,N,Audit Board #1
4,168,,,0.012561523402113088,N,Audit Board #1
4,178,,,0.045506493078700309,N,Audit Board #1
4,184,,,0.057328736557913188,N,Audit Board #1
4,185,,,0.069581494054828042,N,Audit Board #1
4,197,,,0.079527855194555156,N,Audit Board #1
4,207,,,0.020193556889474185,N,Audit Board #1
4,211,,,0.080732090996232546,N,Audit Board #1
7,41,,,0.049935000168388702,N,Audit Board #1
7,47,,,0.044928127597761230,N,Audit Board #1
7,66,,,0.071449550972044642,N,Audit Board #1
7,90,,,0.014480890948814952,N,Audit Board #1
7,97,,,0.000422869909994557,N,Audit Board #1
9,35,,,0.028575144987187110,N,Audit Board #1
9,58,,,0.002239414861789309,N,Audit Board #1
9,60,,,0.088417429762279581,N,Audit Board #1
9,65,,,0.090058075000509540,N,Audit Board #1
9,66,,,0.057133697508910578,N,Audit Board #1
9,75,,,0.005940305956859622,N,Audit Board #1
9,76,,,0.029571656309300808,N,Audit Board #1
9,78,,,0.066056290640459245,N,Audit Board #1
9,82,,,0.030169029311797152,N,Audit Board #1
9,87,,,0.069204096302929209,N,Audit Board #1
9,92,,,0.085740008397800816,N,Audit Board #1
9,103,,,0.017479124138744714,N,Audit Board #1
9,117,,,"0.015073755499525444,0.071754522940001935",N,Audit Board #1
9,120,,,0.069733078505730389,N,Audit Board #1
9,125,,,0.083435111958036862,N,Audit Board #1
9,162,,,0.039105574926248138,N,Audit Board #1
9,167,,,0.076572401921338353,N,Audit Board #1
9,170,,,0.012659967266391661,N,Audit Board #1
9,176,,,0.062920812806473636,N,Audit Board #1
9,178,,,0.015431261678116526,N,Audit Board #1
9,190,,,"0.024942634065142476,0.079568029470118495",N,Audit Board #1
9,205,,,0.004264784574835318,N,Audit Board #1
9,209,,,0.005931925756135669,N,Audit Board #1
9,212,,,"0.014676518443431935,0.029965115310458043",N,Audit Board #1
9,226,,,0.019478257850399899,N,Audit Board #1
9,234,,,0.046644312490909224,N,Audit Board #1
9,235,,,0.075769723057417375,N,Audit Board #1
9,242,,,0.048115489741070131,N,Audit Board #1
9,247,,,0.052251771410321209,N,Audit Board #1
9,251,,,0.080571724573740562,N,Audit Board #1
9,254,,,0.012372409916155587,N,Audit Board #1
9,267,,,0.072672862082360036,N,Audit Board #1
9,280,,,"0.059641462130541641,0.068303669645353141",N,Audit Board #1
9,301,,,0.037462230698154257,N,Audit Board #1
9,322,,,0.040875653021191805,N,Audit Board #1
9,331,,,0.051824848440994189,N,Audit Board #1
9,336,,,0.033869904357900635,N,Audit Board #1
9,342,,,0.041430648875342352,N,Audit Board #1
1,30,,,0.045974803176646675,N,Audit Board #2
1,31,,,0.038473761196091221,N,Audit Board #2
1,42,,,0.072832088863076668,N,Audit Board #2
1,56,,,0.084692321078025708,N,Audit Board #2
1,76,,,0.063689709836951075,N,Audit Board #2
1,77,,,0.010145703501176707,N,Audit Board #2
1,82,,,0.032182577459639822,N,Audit Board #2
1,93,,,0.084948011140671982,N,Audit Board #2
1,112,,,"0.052151395552224451,0.087001115238061781",N,Audit Board #2
10,1,,,0.089705570853357276,N,Audit Board #2
10,2,,,"0.020726848585696222,0.027898446290867704",N,Audit Board #2
10,5,,,0.047704244580727271,N,Audit Board #2
10,7,,,0.055660096862728562,N,Audit Board #2
10,12,,,0.003443858742360291,N,Audit Board #2
10,29,,,0.000726523083586398,N,Audit Board #2
10,30,,,0.079256862757671785,N,Audit Board #2
10,34,,,0.060791594987748783,N,Audit Board #2
10,35,,,0.086814255696821942,N,Audit Board #2
10,40,,,0.080386954982392328,N,Audit Board #2
10,74,,,0.013515621530817076,N,Audit Board #2
10,90,,,0.090325155687605444,N,Audit Board #2
10,91,,,0.039259384605003720,N,Audit Board #2
10,92,,,0.013590837129489085,N,Audit Board #2
10,93,,,0.047499469160839538,N,Audit Board #2
10,96,,,0.090307143476224573,N,Audit Board #2
10,117,,,0.066016716868154979,N,Audit Board #2
10,124,,,0.080206960477668415,N,Audit Board #2
10,129,,,0.005236262767088566,N,Audit Board #2
10,131,,,0.006775266246399606,N,Audit Board #2
10,132,,,0.051803233314723106,N,Audit Board #2
10,134,,,0.072783454048181208,N,Audit Board #2
5,1,,,"0.019890960094355999,0.037375799412196439",N,Audit Board #2
5,4,,,0.017286147560990966,N,Audit Board #2
5,29,,,0.083884961004451931,N,Audit Board #2
5,42,,,0.042686157942574392,N,Audit Board #2
5,48,,,0.032096687877812866,N,Audit Board #2
5,52,,,0.075230157871423850,N,Audit Board #2
5,107,,,0.087737805450180006,N,Audit Board #2
5,114,,,0.029273110368440000,N,Audit Board #2
5,126,,,0.088016505214457400,N,Audit Board #2
5,130,,,0.027832667510471313,N,Audit Board #2
5,135,,,0.062796685408495131,N,Audit Board #2
5,140,,,0.040076077485254714,N,Audit Board #2
5,144,,,"0.014154461848661966,0.084556427898132649",N,Audit Board #2
5,159,,,0.046562710366565021,N,Audit Board #2
5,172,,,0.007517245748707205,N,Audit Board #2
5,173,,,0.066622473484979298,N,Audit Board #2
5,196,,,0.019789300048405073,N,Audit Board #2
5,199,,,0.084429098423218435,N,Audit Board #2
5,204,,,0.032735829827046020,N,Audit Board #2
5,205,,,0.077127168418634544,N,Audit Board #2
5,217,,,0.015325614088755484,N,Audit Board #2
5,222,,,0.073088368846225215,N,Audit Board #2
5,226,,,0.069858216487116617,N,Audit Board #2
6,20,,,0.052650502132812434,N,Audit Board #2
6,23,,,0.024198267339291846,N,Audit Board #2
6,31,,,0.072938796580698499,N,Audit Board #2
6,41,,,"0.067409828981408715,0.091892223376923851",N,Audit Board #2
6,43,,,0.012027652341505312,N,Audit Board #2
6,49,,,0.074713122338604767,N,Audit Board #2
6,70,,,0.077927256128279732,N,Audit Board #2
6,78,,,"0.038840716521686340,0.087754405716602079",N,Audit Board #2
6,102,,,0.032103353020306304,N,Audit Board #2
6,110,,,0.082473117446193688,N,Audit Board #2
6,129,,,0.049479743367166786,N,Audit Board #2
6,143,,,"0.034894131249192128,0.071689460828711230",N,Audit Board #2
6,149,,,0.067361541991678726,N,Audit Board #2
6,153,,,0.028243492967149479,N,Audit Board #2
6,156,,,0.026297323836703481,N,Audit Board #2
6,160,,,0.014968337802530060,N,Audit Board #2
6,179,,,0.065049637397206077,N,Audit Board #2
6,190,,,0.091419854489436702,N,Audit Board #2
6,191,,,0.037080703132364970,N,Audit Board #2
6,227,,,0.065533892357133616,N,Audit Board #2
8,17,,,0.044945281280537394,N,Audit Board #2
8,19,,,0.046824012099359753,N,Audit Board #2
8,64,,,0.014952599777592749,N,Audit Board #2
8,77,,,0.000596883529811021,N,Audit Board #2
8,92,,,0.044046349249398089,N,Audit Board #2
8,99,,,0.002470756366428816,N,Audit Board #2
8,100,,,0.068258005613862456,N,Audit Board #2
8,101,,,0.003431389974703049,N,Audit Board #2
8,103,,,0.058871731806049622,N,Audit Board #2
8,122,,,0.010449387420492501,N,Audit Board #2
8,123,,,0.039266047039467357,N,Audit Board #2
8,128,,,0.024233409285700905,N,Audit Board #2
8,142,,,0.007791157203384555,N,Audit Board #2
8,145,,,0.075594743582597740,N,Audit Board #2
8,146,,,0.058001600533727463,N,Audit Board #2
8,148,,,0.085586631118483573,N,Audit Board #2
8,154,,,0.010169084301720566,N,Audit Board #2
8,162,,,0.000720431479913164,N,Audit Board #2
8,185,,,0.024705314976655067,N,Audit Board #2
8,186,,,0.028614188012983810,N,Audit Board #2
8,194,,,0.038254919798204072,N,Audit Board #2
8,199,,,0.069147874724513093,N,Audit Board #2
8,201,,,0.066170042961875098,N,Audit Board #2
8,204,,,0.047179026035912044,N,Audit Board #2
8,206,,,0.082495574708591235,N,Audit Board #2
8,214,,,0.064418758819236338,N,Audit Board #2
8,227,,,0.072016687453156345,N,Audit Board #2
8,230,,,0.027675301371792092,N,Audit Board #2
"""
