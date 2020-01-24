import os, math, uuid
import tempfile
import json

import pytest

import app
import bgcompute

manifest_file_path = os.path.join(os.path.dirname(__file__), "manifest.csv")
small_manifest_file_path = os.path.join(os.path.dirname(__file__), "small-manifest.csv")

def post_json(client, url, obj):
    return client.post(url, headers = {
        'Content-Type' : 'application/json'
    }, data = json.dumps(obj))

@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        app.init_db()

    yield client

    # clear database between test runs
    app.db.drop_all()
    app.db.create_all()

def test_index(client):
    rv = client.get('/')
    assert b'Arlo (by VotingWorks)' in rv.data

    rv = client.get('/election/1234')
    assert b'Arlo (by VotingWorks)' in rv.data

    rv = client.get('/election/1234/board/5677')
    assert b'Arlo (by VotingWorks)' in rv.data
    
    
def test_whole_audit_flow(client):
    rv = post_json(client, '/election/new', {})
    election_id_1 = json.loads(rv.data)['electionId']
    assert election_id_1

    rv = post_json(client, '/election/new', {})
    election_id_2 = json.loads(rv.data)['electionId']
    assert election_id_2

    print("running whole audit flow " + election_id_1)
    run_whole_audit_flow(client, election_id_1, "Primary 2019", 10, "12345678901234567890")

    print("running whole audit flow " + election_id_2)    
    run_whole_audit_flow(client, election_id_2, "General 2019", 5, "12345678901234599999")

    # after resetting election 1, election 2 is still around
    run_election_reset(client, election_id_1)

    rv = client.get('/election/{}/audit/status'.format(election_id_2))
    result2 = json.loads(rv.data)
    assert result2["riskLimit"] == 5

def setup_whole_audit(client, election_id, name, risk_limit, random_seed):
    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())    

    url_prefix = "/election/{}".format(election_id)

    rv = post_json(
        client, '{}/audit/basic'.format(url_prefix),
        {
            "name" : name,
            "riskLimit" : risk_limit,
            "randomSeed": random_seed,

            "contests" : [
                {
                    "id": contest_id,
                    "name": "contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "candidate 1",
                            "numVotes": 48121
                        },
                        {
                            "id": candidate_id_2,
                            "name": "candidate 2",
                            "numVotes": 38026
                        }                        
                    ],

                    "totalBallotsCast": 86147,
                    "numWinners": 1,
                    "votesAllowed": 1
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    # before background compute, should be null sample size options
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    assert status["rounds"][0]["contests"][0]["sampleSizeOptions"] is None

    # after background compute
    bgcompute.bgcompute()
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    assert len(status["rounds"][0]["contests"][0]["sampleSizeOptions"]) == 4
    
    assert status["randomSeed"] == random_seed
    assert len(status["contests"]) == 1
    assert status["riskLimit"] == risk_limit
    assert status["name"] == name

    assert status["contests"][0]["choices"][0]["id"] == candidate_id_1

    rv = post_json(
        client, '{}/audit/jurisdictions'.format(url_prefix),
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
                            "members": []
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "audit board #2",
                            "members": []
                        }
                    ]
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "adams county"
    assert jurisdiction["auditBoards"][1]["name"] == "audit board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_90 = [option for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"] if option["prob"] == 0.9]
    assert len(sample_size_90) == 1
    sample_size = sample_size_90[0]["size"]

    # set the sample_size
    rv = post_json(client, '{}/audit/sample-size'.format(url_prefix), {
        "size": sample_size
    })

    assert json.loads(rv.data)["status"] == "ok"

    # upload the manifest
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id), data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'manifest.csv'
    assert manifest['numBallots'] == 86147
    assert manifest['numBatches'] == 484
    assert manifest['uploadedAt']

    # delete the manifest and make sure that works
    rv = client.delete('{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id))
    assert json.loads(rv.data)['status'] == "ok"

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']

    assert manifest['filename'] is None
    assert manifest['uploadedAt'] is None

    # upload the manifest again
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id), data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    # get the retrieval list for round 1
    rv = client.get('{}/jurisdiction/{}/1/retrieval-list'.format(url_prefix, jurisdiction_id))
    lines = rv.data.decode('utf-8').splitlines()
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert len(lines) > 5
    assert 'attachment' in rv.headers['content-disposition']

    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])

    return url_prefix, contest_id, candidate_id_1, candidate_id_2, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots
    
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
        client, '{}/audit/basic'.format(url_prefix),
        {
            "name" : name,
            "riskLimit" : risk_limit,
            "randomSeed": random_seed,

            "contests" : [
                {
                    "id": contest_id,
                    "name": "contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "candidate 1",
                            "numVotes": 43121
                        },
                        {
                            "id": candidate_id_2,
                            "name": "candidate 2",
                            "numVotes": 38026
                        },   
                        {
                            "id": candidate_id_3,
                            "name": "candidate 3",
                            "numVotes": 5000 
                        },   

                    ],

                    "totalBallotsCast": 86147,
                    "numWinners": 2,
                    "votesAllowed": 1
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    # before background compute, should be null sample size options
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    assert status["rounds"][0]["contests"][0]["sampleSizeOptions"] is None

    # after background compute
    bgcompute.bgcompute()
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    # We should only get the expected sample size for multi-winner
    assert len(status["rounds"][0]["contests"][0]["sampleSizeOptions"]) == 1
    
    assert status["randomSeed"] == random_seed
    assert len(status["contests"]) == 1
    assert status["riskLimit"] == risk_limit
    assert status["name"] == name

    assert status["contests"][0]["choices"][0]["id"] == candidate_id_1

    rv = post_json(
        client, '{}/audit/jurisdictions'.format(url_prefix),
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
                            "members": []
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "audit board #2",
                            "members": []
                        }
                    ]
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "adams county"
    assert jurisdiction["auditBoards"][1]["name"] == "audit board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_asn = [option for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"]]
    assert len(sample_size_asn) == 1
    sample_size = sample_size_asn[0]["size"]

    # set the sample_size
    rv = post_json(client, '{}/audit/sample-size'.format(url_prefix), {
        "size": sample_size
    })

    assert json.loads(rv.data)["status"] == "ok"

    # upload the manifest
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id), data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'manifest.csv'
    assert manifest['numBallots'] == 86147
    assert manifest['numBatches'] == 484
    assert manifest['uploadedAt']

    # delete the manifest and make sure that works
    rv = client.delete('{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id))
    assert json.loads(rv.data)['status'] == "ok"

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']

    assert manifest['filename'] is None
    assert manifest['uploadedAt'] is None

    # upload the manifest again
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '{}/jurisdiction/{}/manifest'.format(url_prefix, jurisdiction_id), data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    # get the retrieval list for round 1
    rv = client.get('{}/jurisdiction/{}/1/retrieval-list'.format(url_prefix, jurisdiction_id))
    lines = rv.data.decode('utf-8').split("\r\n")
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert len(lines) > 5
    assert 'attachment' in rv.headers['content-disposition']

    rows = [line.split(",") for line in lines[1:] if line!=""]
    num_ballots = sum([int(row[4]) for row in rows])

    return url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots
    
def run_whole_audit_flow(client, election_id, name, risk_limit, random_seed):
    url_prefix, contest_id, candidate_id_1, candidate_id_2, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_audit(client, election_id, name, risk_limit, random_seed)
    
    # post results for round 1
    num_for_winner = int(num_ballots * 0.56)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(client, '{}/jurisdiction/{}/1/results'.format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser
                    }
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
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
    rv = client.post('{}/audit/reset'.format(url_prefix))
    response = json.loads(rv.data)
    assert response['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)

    assert status["riskLimit"] == None
    assert status["randomSeed"] == None
    assert status["contests"] == []
    assert status["jurisdictions"] == []
    assert status["rounds"] == []        
    
def test_small_election(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    rv = post_json(
        client, f'/election/{election_id}/audit/basic',
        {
            "name" : "Small Test 2019",
            "riskLimit" : 10,
            "randomSeed": "a1234567890987654321b",

            "contests" : [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "Candidate 1",
                            "numVotes": 1325
                        },
                        {
                            "id": candidate_id_2,
                            "name": "Candidate 2",
                            "numVotes": 792
                        }                        
                    ],

                    "totalBallotsCast": 2123,
                    "numWinners": 1,
                    "votesAllowed": 1
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    bgcompute.bgcompute()
    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)

    assert status["name"] == "Small Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())

    rv = post_json(
        client, f'/election/{election_id}/audit/jurisdictions',
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
                            "members": []
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "Audit Board #2",
                            "members": []
                        }
                    ]
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "County 1"
    assert jurisdiction["auditBoards"][1]["name"] == "Audit Board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_90 = [option for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"] if option["prob"] == 0.9]
    assert len(sample_size_90) == 1
    sample_size = sample_size_90[0]["size"]

    # set the sample_size
    rv = post_json(client, f'/election/{election_id}/audit/sample-size', {
        "size": sample_size
    })
    
    # upload the manifest
    data = {}
    data['manifest'] = (open(small_manifest_file_path, "rb"), 'small-manifest.csv')
    rv = client.post(
        f'/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest', data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'small-manifest.csv'
    assert manifest['numBallots'] == 2117
    assert manifest['numBatches'] == 10
    assert manifest['uploadedAt']

    # get the retrieval list for round 1
    rv = client.get(f'/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list')

    # deterministic sampling, should be the same every time, tweak for CRLF
    assert rv.data.decode('utf-8').replace("\r\n","\n") == EXPECTED_RETRIEVAL_LIST
    
    lines = rv.data.decode('utf-8').splitlines()
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(client, f'/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results',
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser
                    }
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f'/election/{election_id}/audit/report')
    lines = rv.data.decode('utf-8').splitlines()
    assert lines[0] == "Contest Name,Contest 1"
    assert 'attachment' in rv.headers['Content-Disposition']


def test_contest_choices_cannot_have_more_votes_than_allowed(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())

    # bad request, 21 + 40 actual votes > 30 * 2 allowed votes
    rv = post_json(
        client, f'/election/{election_id}/audit/basic',
        {
            "name" : "Small Test 2019",
            "riskLimit" : 10,
            "randomSeed": "a1234567890987654321b",

            "contests" : [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "Candidate 1",
                            "numVotes": 21
                        },
                        {
                            "id": candidate_id_2,
                            "name": "Candidate 2",
                            "numVotes": 40
                        }                        
                    ],

                    "totalBallotsCast": 30,
                    "numWinners": 1,
                    "votesAllowed": 2
                }
            ]
        })

    response = json.loads(rv.data)
    assert response == {
        'errors': [
            {
                'message': 'Too many votes cast in contest: Contest 1 (61 votes, 60 allowed)',
                'errorType': 'TooManyVotes'
            }
        ]
    }

    # good request, 20 + 40 actual votes <= 30 * 2 allowed votes
    rv = post_json(
        client, f'/election/{election_id}/audit/basic',
        {
            "name" : "Small Test 2019",
            "riskLimit" : 10,
            "randomSeed": "a1234567890987654321b",

            "contests" : [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "Candidate 1",
                            "numVotes": 20
                        },
                        {
                            "id": candidate_id_2,
                            "name": "Candidate 2",
                            "numVotes": 40
                        }                        
                    ],

                    "totalBallotsCast": 30,
                    "numWinners": 1,
                    "votesAllowed": 2
                }
            ]
        })

    response = json.loads(rv.data)
    assert response == { 'status': 'ok' }

def test_multi_round_audit(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_audit(client, election_id, 'Multi-Round Audit', 10, '32423432423432')

    # post results for round 1 with 50/50 split, should not complete.
    num_for_winner = int(num_ballots * 0.5)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(client, '{}/jurisdiction/{}/1/results'.format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser
                    }
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
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
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)

    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"]
    assert status["rounds"][1]["contests"][0]["sampleSize"]    

    # round 2 retrieval list should be ready
    rv = client.get('{}/jurisdiction/{}/2/retrieval-list'.format(url_prefix, jurisdiction_id))
    lines = rv.data.decode('utf-8').splitlines()
    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])
    assert num_ballots == status["rounds"][1]["contests"][0]["sampleSize"]
    
@pytest.mark.quick
def test_multi_winner_election(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    contest_id = str(uuid.uuid4())
    candidate_id_1 = str(uuid.uuid4())
    candidate_id_2 = str(uuid.uuid4())
    candidate_id_3 = str(uuid.uuid4())

    rv = post_json(
        client, f'/election/{election_id}/audit/basic',
        {
            "name" : "Small Multi-winner Test 2019",
            "riskLimit" : 10,
            "randomSeed": "a1234567890987654321b",

            "contests" : [
                {
                    "id": contest_id,
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "Candidate 1",
                            "numVotes": 1000
                        },
                        {
                            "id": candidate_id_2,
                            "name": "Candidate 2",
                            "numVotes": 792
                        },
                        {
                            "id": candidate_id_3,
                            "name": "Candidate 3",
                            "numVotes": 331
                        },

                    ],

                    "totalBallotsCast": 2123,
                    "numWinners": 2,
                    "votesAllowed": 1
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    bgcompute.bgcompute()
    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)

    assert status["name"] == "Small Multi-winner Test 2019"

    jurisdiction_id = str(uuid.uuid4())
    audit_board_id_1 = str(uuid.uuid4())
    audit_board_id_2 = str(uuid.uuid4())    

    rv = post_json(
        client, f'/election/{election_id}/audit/jurisdictions',
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
                            "members": []
                        },
                        {
                            "id": audit_board_id_2,
                            "name": "Audit Board #2",
                            "members": []
                        }
                    ]
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "County 1"
    assert jurisdiction["auditBoards"][1]["name"] == "Audit Board #2"
    assert jurisdiction["contests"] == [contest_id]

    # choose a sample size
    sample_size_asn = [option for option in status["rounds"][0]["contests"][0]["sampleSizeOptions"]]
    assert len(sample_size_asn) == 1
    sample_size = sample_size_asn[0]["size"]

    # set the sample_size
    rv = post_json(client, f'/election/{election_id}/audit/sample-size', {
        "size": sample_size
    })
    
    # upload the manifest
    data = {}
    data['manifest'] = (open(small_manifest_file_path, "rb"), 'small-manifest.csv')
    rv = client.post(
        f'/election/{election_id}/jurisdiction/{jurisdiction_id}/manifest', data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'small-manifest.csv'
    assert manifest['numBallots'] == 2117
    assert manifest['numBatches'] == 10
    assert manifest['uploadedAt']

    # get the retrieval list for round 1
    rv = client.get(f'/election/{election_id}/jurisdiction/{jurisdiction_id}/1/retrieval-list')
    lines = rv.data.decode('utf-8').split("\r\n")
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_winner2 = int(num_ballots * 0.3)
    num_for_loser = num_ballots - num_for_winner - num_for_winner2
    rv = post_json(client, f'/election/{election_id}/jurisdiction/{jurisdiction_id}/1/results',
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_winner2,
                        candidate_id_3: num_for_loser
                    }
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get(f'/election/{election_id}/audit/status')
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == contest_id
    assert round_contest["results"][candidate_id_1] == num_for_winner
    assert round_contest["results"][candidate_id_2] == num_for_winner2
    assert round_contest["results"][candidate_id_3] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

    rv = client.get(f'/election/{election_id}/audit/report')
    lines = rv.data.decode('utf-8').split("\r\n")
    assert lines[0] == "Contest Name,Contest 1"
    assert 'attachment' in rv.headers['Content-Disposition']
    

def test_multi_round_multi_winner_audit(client):
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_multi_winner_audit(client, election_id, 'Multi-Round Multi-winner Audit', 10, '32423432423432')

    # post results for round 1 with 50/50 split, should not complete.
    num_for_winner = int(num_ballots * 0.4)
    num_for_winner2 = int(num_ballots*0.4)
    num_for_loser = num_ballots - num_for_winner - num_for_winner2
    rv = post_json(client, '{}/jurisdiction/{}/1/results'.format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_winner2,
                        candidate_id_3: num_for_loser,
                    }
                }
            ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('{}/audit/status'.format(url_prefix))
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
    rv = client.get('{}/audit/status'.format(url_prefix))
    status = json.loads(rv.data)

    assert status["rounds"][1]["contests"][0]["sampleSizeOptions"]
    assert status["rounds"][1]["contests"][0]["sampleSize"]    

    # round 2 retrieval list should be ready
    rv = client.get('{}/jurisdiction/{}/2/retrieval-list'.format(url_prefix, jurisdiction_id))
    lines = rv.data.decode('utf-8').split("\r\n")
    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])
    assert num_ballots == status["rounds"][1]["contests"][0]["sampleSize"]

def test_ballot_set(client):
    ## setup
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_multi_winner_audit(client, election_id, 'Multi-Round Multi-winner Audit', 10, '32423432423432')

    ## find a sampled ballot to update
    rv = client.get('{}/audit/status'.format(url_prefix))
    response = json.loads(rv.data)
    jurisdiction = [j for j in response['jurisdictions'] if j['id'] == jurisdiction_id][0]
    rounds = response['rounds']
    batch_id = None
    round_id = None
    ballot = None

    for round in rounds:
        rv = client.get('{}/jurisdiction/{}/round/{}/ballot-list'.format(url_prefix, jurisdiction_id, round['id']))
        response = json.loads(rv.data)

        if response['ballots']:
            ballot = response['ballots'][0]
            batch_id = ballot['batch']['id']
            round_id = round['id']
            assert not ballot['status']
            assert not ballot['vote']
            assert not ballot['comment']
            break

    assert batch_id is not None
    assert round_id is not None
    assert ballot is not None

    ## set the ballot data
    url = '{}/jurisdiction/{}/batch/{}/round/{}/ballot/{}'.format(url_prefix, jurisdiction_id, batch_id, round_id, ballot['position'])

    rv = post_json(client, url, { 'vote': 'NO', 'comment': 'This one had a hanging chad.' })
    response = json.loads(rv.data)

    assert response['status'] == 'ok'

    ## verify the update actually did something
    rv = client.get('{}/jurisdiction/{}/round/{}/ballot-list'.format(url_prefix, jurisdiction_id, round_id))
    response = json.loads(rv.data)
    ballot_position = ballot['position']
    ballot = [b for b in response['ballots'] if b['position'] == ballot_position][0]

    assert ballot['status'] == 'AUDITED'
    assert ballot['vote'] == 'NO'
    assert ballot['comment'] == 'This one had a hanging chad.'

def test_ballot_list_ordering(client):
    ## setup
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_multi_winner_audit(client, election_id, 'Multi-Round Multi-winner Audit', 10, '32423432423432')

    ## find all rounds for this jurisdiction
    rv = client.get('{}/audit/status'.format(url_prefix))
    response = json.loads(rv.data)
    jurisdiction = [j for j in response['jurisdictions'] if j['id'] == jurisdiction_id][0]
    rounds = response['rounds']

    ## verify order of all returned ballots
    for round in rounds:
        rv = client.get('{}/jurisdiction/{}/round/{}/ballot-list'.format(url_prefix, jurisdiction_id, round['id']))
        response = json.loads(rv.data)

        unsorted_ballots = response['ballots']
        sorted_ballots = sorted(
            unsorted_ballots,
            key=lambda ballot: (ballot['auditBoard']['name'], ballot['batch']['name'], ballot['position'])
        )

        assert unsorted_ballots == sorted_ballots

def test_ballot_list_ordering_by_audit_board(client):
    ## setup
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_multi_winner_audit(client, election_id, 'Multi-Round Multi-winner Audit', 10, '32423432423432')

    ## find all rounds for this jurisdiction
    rv = client.get('{}/audit/status'.format(url_prefix))
    response = json.loads(rv.data)
    jurisdiction = [j for j in response['jurisdictions'] if j['id'] == jurisdiction_id][0]
    rounds = response['rounds']

    ## verify order of all returned ballots
    for round in rounds:
        rv = client.get('{}/jurisdiction/{}/audit-board/{}/round/{}/ballot-list'.format(url_prefix, jurisdiction_id, audit_board_id_1, round['id']))
        response = json.loads(rv.data)

        unsorted_ballots = response['ballots']
        sorted_ballots = sorted(
            unsorted_ballots,
            key=lambda ballot: (ballot['batch']['name'], ballot['position'])
        )

        assert unsorted_ballots == sorted_ballots

def test_audit_board(client):
    ## setup
    rv = post_json(client, '/election/new', {})
    election_id = json.loads(rv.data)['electionId']

    url_prefix, contest_id, candidate_id_1, candidate_id_2, candidate_id_3, jurisdiction_id, audit_board_id_1, audit_board_id_2, num_ballots = setup_whole_multi_winner_audit(client, election_id, 'Multi-Round Multi-winner Audit', 10, '32423432423432')
    url = '{}/jurisdiction/{}/audit-board/{}'.format(url_prefix, jurisdiction_id, audit_board_id_1)

    ## check audit board
    rv = client.get(url)
    response = json.loads(rv.data)

    assert response['id'] == audit_board_id_1
    assert response['name']
    assert response['members'] == []

    ## submit new data
    rv = post_json(client, url, {
        'name': 'Awesome Audit Board',
        'members': [
            { 'name': 'Darth Vader', 'affiliation': 'EMP' },
            { 'name': 'Leia Organa', 'affiliation': 'REB' }
        ]
    })
    response = json.loads(rv.data)

    assert response['status'] == 'ok'

    ## check new data
    rv = client.get(url)
    response = json.loads(rv.data)

    assert response['id'] == audit_board_id_1
    assert response['name'] == 'Awesome Audit Board'
    assert response['members'] == [
        { 'name': 'Darth Vader', 'affiliation': 'EMP' },
        { 'name': 'Leia Organa', 'affiliation': 'REB' }
    ]


EXPECTED_RETRIEVAL_LIST = """Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board
3,4,,,1,Audit Board #1
3,31,,,1,Audit Board #1
3,33,,,1,Audit Board #1
3,35,,,1,Audit Board #1
3,44,,,1,Audit Board #1
3,47,,,1,Audit Board #1
3,59,,,1,Audit Board #1
3,80,,,1,Audit Board #1
3,85,,,1,Audit Board #1
3,88,,,2,Audit Board #1
3,93,,,1,Audit Board #1
3,117,,,1,Audit Board #1
3,139,,,1,Audit Board #1
3,154,,,1,Audit Board #1
3,167,,,1,Audit Board #1
3,171,,,1,Audit Board #1
3,176,,,2,Audit Board #1
4,2,,,1,Audit Board #1
4,17,,,1,Audit Board #1
4,23,,,1,Audit Board #1
4,24,,,1,Audit Board #1
4,25,,,1,Audit Board #1
4,37,,,1,Audit Board #1
4,54,,,1,Audit Board #1
4,92,,,1,Audit Board #1
4,95,,,1,Audit Board #1
4,113,,,1,Audit Board #1
4,129,,,1,Audit Board #1
4,140,,,1,Audit Board #1
4,143,,,1,Audit Board #1
4,168,,,1,Audit Board #1
4,178,,,1,Audit Board #1
4,184,,,1,Audit Board #1
4,185,,,1,Audit Board #1
4,197,,,1,Audit Board #1
4,207,,,1,Audit Board #1
4,211,,,1,Audit Board #1
5,1,,,2,Audit Board #1
5,4,,,1,Audit Board #1
5,29,,,1,Audit Board #1
5,42,,,1,Audit Board #1
5,48,,,1,Audit Board #1
5,52,,,1,Audit Board #1
5,107,,,1,Audit Board #1
5,114,,,1,Audit Board #1
5,126,,,1,Audit Board #1
5,130,,,1,Audit Board #1
5,135,,,1,Audit Board #1
5,140,,,1,Audit Board #1
5,144,,,2,Audit Board #1
5,159,,,1,Audit Board #1
5,172,,,1,Audit Board #1
5,173,,,1,Audit Board #1
5,196,,,1,Audit Board #1
5,199,,,1,Audit Board #1
5,204,,,1,Audit Board #1
5,205,,,1,Audit Board #1
5,217,,,1,Audit Board #1
5,222,,,1,Audit Board #1
5,226,,,1,Audit Board #1
7,41,,,1,Audit Board #1
7,47,,,1,Audit Board #1
7,66,,,1,Audit Board #1
7,90,,,1,Audit Board #1
7,97,,,1,Audit Board #1
9,35,,,1,Audit Board #1
9,58,,,1,Audit Board #1
9,60,,,1,Audit Board #1
9,65,,,1,Audit Board #1
9,66,,,1,Audit Board #1
9,75,,,1,Audit Board #1
9,76,,,1,Audit Board #1
9,78,,,1,Audit Board #1
9,82,,,1,Audit Board #1
9,87,,,1,Audit Board #1
9,92,,,1,Audit Board #1
9,103,,,1,Audit Board #1
9,117,,,2,Audit Board #1
9,120,,,1,Audit Board #1
9,125,,,1,Audit Board #1
9,162,,,1,Audit Board #1
9,167,,,1,Audit Board #1
9,170,,,1,Audit Board #1
9,176,,,1,Audit Board #1
9,178,,,1,Audit Board #1
9,190,,,2,Audit Board #1
9,205,,,1,Audit Board #1
9,209,,,1,Audit Board #1
9,212,,,2,Audit Board #1
9,226,,,1,Audit Board #1
9,234,,,1,Audit Board #1
9,235,,,1,Audit Board #1
9,242,,,1,Audit Board #1
9,247,,,1,Audit Board #1
9,251,,,1,Audit Board #1
9,254,,,1,Audit Board #1
9,267,,,1,Audit Board #1
9,280,,,2,Audit Board #1
9,301,,,1,Audit Board #1
9,322,,,1,Audit Board #1
9,331,,,1,Audit Board #1
9,336,,,1,Audit Board #1
9,342,,,1,Audit Board #1
1,30,,,1,Audit Board #2
1,31,,,1,Audit Board #2
1,42,,,1,Audit Board #2
1,56,,,1,Audit Board #2
1,76,,,1,Audit Board #2
1,77,,,1,Audit Board #2
1,82,,,1,Audit Board #2
1,93,,,1,Audit Board #2
1,112,,,2,Audit Board #2
10,1,,,1,Audit Board #2
10,2,,,2,Audit Board #2
10,5,,,1,Audit Board #2
10,7,,,1,Audit Board #2
10,12,,,1,Audit Board #2
10,29,,,1,Audit Board #2
10,30,,,1,Audit Board #2
10,34,,,1,Audit Board #2
10,35,,,1,Audit Board #2
10,40,,,1,Audit Board #2
10,74,,,1,Audit Board #2
10,90,,,1,Audit Board #2
10,91,,,1,Audit Board #2
10,92,,,1,Audit Board #2
10,93,,,1,Audit Board #2
10,96,,,1,Audit Board #2
10,117,,,1,Audit Board #2
10,124,,,1,Audit Board #2
10,129,,,1,Audit Board #2
10,131,,,1,Audit Board #2
10,132,,,1,Audit Board #2
10,134,,,1,Audit Board #2
2,1,,,1,Audit Board #2
2,12,,,1,Audit Board #2
2,15,,,1,Audit Board #2
2,33,,,1,Audit Board #2
2,37,,,1,Audit Board #2
2,77,,,1,Audit Board #2
2,78,,,1,Audit Board #2
2,93,,,1,Audit Board #2
2,107,,,2,Audit Board #2
2,117,,,1,Audit Board #2
2,123,,,1,Audit Board #2
2,124,,,1,Audit Board #2
2,136,,,1,Audit Board #2
2,144,,,1,Audit Board #2
2,182,,,1,Audit Board #2
2,194,,,2,Audit Board #2
2,199,,,1,Audit Board #2
2,209,,,1,Audit Board #2
2,224,,,1,Audit Board #2
2,226,,,1,Audit Board #2
2,232,,,1,Audit Board #2
2,261,,,1,Audit Board #2
2,263,,,1,Audit Board #2
6,20,,,1,Audit Board #2
6,23,,,1,Audit Board #2
6,31,,,1,Audit Board #2
6,41,,,2,Audit Board #2
6,43,,,1,Audit Board #2
6,49,,,1,Audit Board #2
6,70,,,1,Audit Board #2
6,78,,,2,Audit Board #2
6,102,,,1,Audit Board #2
6,110,,,1,Audit Board #2
6,129,,,1,Audit Board #2
6,143,,,2,Audit Board #2
6,149,,,1,Audit Board #2
6,153,,,1,Audit Board #2
6,156,,,1,Audit Board #2
6,160,,,1,Audit Board #2
6,179,,,1,Audit Board #2
6,190,,,1,Audit Board #2
6,191,,,1,Audit Board #2
6,227,,,1,Audit Board #2
8,17,,,1,Audit Board #2
8,19,,,1,Audit Board #2
8,64,,,1,Audit Board #2
8,77,,,1,Audit Board #2
8,92,,,1,Audit Board #2
8,99,,,1,Audit Board #2
8,100,,,1,Audit Board #2
8,101,,,1,Audit Board #2
8,103,,,1,Audit Board #2
8,122,,,1,Audit Board #2
8,123,,,1,Audit Board #2
8,128,,,1,Audit Board #2
8,142,,,1,Audit Board #2
8,145,,,1,Audit Board #2
8,146,,,1,Audit Board #2
8,148,,,1,Audit Board #2
8,154,,,1,Audit Board #2
8,162,,,1,Audit Board #2
8,185,,,1,Audit Board #2
8,186,,,1,Audit Board #2
8,194,,,1,Audit Board #2
8,199,,,1,Audit Board #2
8,201,,,1,Audit Board #2
8,204,,,1,Audit Board #2
8,206,,,1,Audit Board #2
8,214,,,1,Audit Board #2
8,227,,,1,Audit Board #2
8,230,,,1,Audit Board #2
"""
