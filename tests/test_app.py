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

def test_index(client):
    rv = client.get('/')
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
                    "winners": 1
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
                    "winners": 2
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
                    "winners": 1,
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
                    "winners": 2,
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
