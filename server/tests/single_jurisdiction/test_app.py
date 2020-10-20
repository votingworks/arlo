import os, math, uuid
import json, csv, io
from flask.testing import FlaskClient
import pytest

from ..helpers import assert_ok, post_json, create_election
from ... import bgcompute

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

    rv = client.get("/api/election/{}/audit/status".format(election_id_2))
    result2 = json.loads(rv.data)
    assert result2["riskLimit"] == 5


def setup_audit_board(client, election_id, jurisdiction_id, audit_board_id):
    rv = post_json(
        client,
        "/api/election/{}/jurisdiction/{}/audit-board/{}".format(
            election_id, jurisdiction_id, audit_board_id
        ),
        {
            "name": "Audit Board #1",
            "members": [
                {"name": "Joe Schmo", "affiliation": "REP"},
                {"name": "Jane Plain", "affiliation": None},
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

    url_prefix = "/api/election/{}".format(election_id)

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
    bgcompute.bgcompute_update_ballot_manifest_file()

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
    bgcompute.bgcompute_update_ballot_manifest_file()

    setup_audit_board(client, election_id, jurisdiction_id, audit_board_id_1)

    # get the retrieval list for round 1
    rv = client.get(
        "{}/jurisdiction/{}/1/retrieval-list".format(url_prefix, jurisdiction_id)
    )
    lines = rv.data.decode("utf-8").splitlines()
    assert (
        lines[0]
        == "Container,Tabulator,Batch Name,Ballot Number,Ticket Numbers,Already Audited,Audit Board"
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

    url_prefix = "/api/election/{}".format(election_id)

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
    bgcompute.bgcompute_update_ballot_manifest_file()

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
    bgcompute.bgcompute_update_ballot_manifest_file()

    # get the retrieval list for round 1
    rv = client.get(
        "{}/jurisdiction/{}/1/retrieval-list".format(url_prefix, jurisdiction_id)
    )
    lines = rv.data.decode("utf-8").split("\r\n")
    assert (
        lines[0]
        == "Container,Tabulator,Batch Name,Ballot Number,Ticket Numbers,Already Audited,Audit Board"
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
    url_prefix = "/api/election/{}".format(election_id)

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
    return sum([len(line["Ticket Numbers"].split(",")) for line in lines])


def test_small_election(client, election_id, snapshot):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/api/election/{election_id}/audit/basic",
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
    rv = client.get(f"/api/election/{election_id}/audit/status")
    assert not json.loads(rv.data)["frozenAt"]

    rv = client.post(f"/api/election/{election_id}/audit/freeze")
    assert_ok(rv)

    # now frozen
    rv = client.get(f"/api/election/{election_id}/audit/status")
    frozen_at = json.loads(rv.data)["frozenAt"]
    assert frozen_at

    # make sure freezing twice doesn't change frozen date
    rv = client.post(f"/api/election/{election_id}/audit/freeze")
    rv = client.get(f"/api/election/{election_id}/audit/status")
    frozen_at_2 = json.loads(rv.data)["frozenAt"]

    assert frozen_at == frozen_at_2

    bgcompute.bgcompute()

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["name"] == "Small Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/api/election/{election_id}/audit/jurisdictions",
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

    rv = client.get(f"/api/election/{election_id}/audit/status")
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
        client, f"/api/election/{election_id}/audit/sample-size", {"size": sample_size}
    )

    # upload the manifest
    data = {}
    data["manifest"] = (open(small_manifest_file_path, "rb"), "small-manifest.csv")
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest",
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    bgcompute.bgcompute_update_ballot_manifest_file()

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 2117
    assert manifest["numBatches"] == 10
    assert manifest["file"]["name"] == "small-manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # get the retrieval list for round 1
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list"
    )

    # deterministic sampling, should be the same every time, tweak for CRLF
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    lines = retrieval_list.splitlines()
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Ticket Numbers,Already Audited,Audit Board"
    )
    assert "attachment" in rv.headers["Content-Disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results",
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

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f"/api/election/{election_id}/report")
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
        f"/api/election/{election_id}/audit/basic",
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
        f"/api/election/{election_id}/audit/basic",
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


def test_multi_round_audit(client, election_id, snapshot):
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
    snapshot.assert_match(already_audited)


def test_multi_winner_election(client, election_id):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    candidate_id_3 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/api/election/{election_id}/audit/basic",
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

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    assert status["name"] == "Small Multi-winner Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    rv = post_json(
        client,
        f"/api/election/{election_id}/audit/jurisdictions",
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

    rv = client.post(f"/api/election/{election_id}/audit/freeze")
    assert_ok(rv)
    bgcompute.bgcompute()

    rv = client.get(f"/api/election/{election_id}/audit/status")
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
        client, f"/api/election/{election_id}/audit/sample-size", {"size": sample_size}
    )

    # upload the manifest
    data = {}
    data["manifest"] = (open(small_manifest_file_path, "rb"), "small-manifest.csv")
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest",
        data=data,
        content_type="multipart/form-data",
    )

    assert_ok(rv)
    bgcompute.bgcompute_update_ballot_manifest_file()

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    manifest = status["jurisdictions"][0]["ballotManifest"]

    assert manifest["numBallots"] == 2117
    assert manifest["numBatches"] == 10
    assert manifest["file"]["name"] == "small-manifest.csv"
    assert manifest["file"]["uploadedAt"]

    # get the retrieval list for round 1
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list"
    )
    lines = rv.data.decode("utf-8").split("\r\n")
    assert (
        lines[0]
        == "Batch Name,Ballot Number,Ticket Numbers,Already Audited,Audit Board"
    )
    assert "attachment" in rv.headers["Content-Disposition"]

    num_ballots = get_num_ballots_from_retrieval_list(rv)

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_winner2 = int(num_ballots * 0.3)
    num_for_loser = num_ballots - num_for_winner - num_for_winner2
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results",
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

    rv = client.get(f"/api/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_winner2
    assert round_contest["results"][candidate_id_3] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f"/api/election/{election_id}/report")
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
                    "choiceIds": [candidate_id_1],
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
            "choiceIds": [candidate_id_1],
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
                {"name": "Darth Vader", "affiliation": "REP"},
                {"name": "Leia Organa", "affiliation": "DEM"},
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
        {"name": "Darth Vader", "affiliation": "REP"},
        {"name": "Leia Organa", "affiliation": "DEM"},
    ]
