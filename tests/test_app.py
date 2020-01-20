import os, math, uuid
import tempfile
import json, csv, io

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
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    assert len(lines) > 5
    assert 'attachment' in rv.headers['content-disposition']

    num_ballots = get_num_ballots_from_retrieval_list(rv)

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
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    assert len(lines) > 5
    assert 'attachment' in rv.headers['content-disposition']

    num_ballots = get_num_ballots_from_retrieval_list(rv)

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

def get_num_ballots_from_retrieval_list(rv):
    lines = csv.DictReader(io.StringIO(rv.data.decode('utf-8')))
    return sum([len(line['Ticket Numbers'].split(',')) for line in lines])
    
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
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = get_num_ballots_from_retrieval_list(rv)

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

    # Count the ticket numbers
    num_ballots = get_num_ballots_from_retrieval_list(rv)

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
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = get_num_ballots_from_retrieval_list(rv)

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
    num_ballots = get_num_ballots_from_retrieval_list(rv)
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
    url = '{}/jurisdiction/{}/batch/{}/ballot/{}'.format(url_prefix, jurisdiction_id, batch_id, ballot['position'])

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


EXPECTED_RETRIEVAL_LIST = """Batch Name,Ballot Number,Storage Location,Tabulator,Ticket Numbers,Already Audited,Audit Board
2,1,,,0.051285890,N,Audit Board #1
2,12,,,0.039500694,N,Audit Board #1
2,15,,,0.022297876,N,Audit Board #1
2,33,,,0.083437628,N,Audit Board #1
2,37,,,0.049404132,N,Audit Board #1
2,77,,,0.011444765,N,Audit Board #1
2,78,,,0.065235158,N,Audit Board #1
2,93,,,0.085982349,N,Audit Board #1
2,107,,,"0.055192852,0.062597461",N,Audit Board #1
2,117,,,0.079468520,N,Audit Board #1
2,123,,,0.026064338,N,Audit Board #1
2,124,,,0.009739290,N,Audit Board #1
2,136,,,0.061799951,N,Audit Board #1
2,144,,,0.091785694,N,Audit Board #1
2,182,,,0.074618452,N,Audit Board #1
2,194,,,"0.047151231,0.075256824",N,Audit Board #1
2,199,,,0.026376966,N,Audit Board #1
2,209,,,0.080512568,N,Audit Board #1
2,224,,,0.067184755,N,Audit Board #1
2,226,,,0.045082075,N,Audit Board #1
2,232,,,0.070914470,N,Audit Board #1
2,261,,,0.076081179,N,Audit Board #1
2,263,,,0.060659269,N,Audit Board #1
3,4,,,0.061537690,N,Audit Board #1
3,31,,,0.029862723,N,Audit Board #1
3,33,,,0.063033033,N,Audit Board #1
3,35,,,0.088031358,N,Audit Board #1
3,44,,,0.062288103,N,Audit Board #1
3,47,,,0.027294463,N,Audit Board #1
3,59,,,0.001909776,N,Audit Board #1
3,80,,,0.087253393,N,Audit Board #1
3,85,,,0.048683168,N,Audit Board #1
3,88,,,"0.028211968,0.031651590",N,Audit Board #1
3,93,,,0.048579436,N,Audit Board #1
3,117,,,0.065532510,N,Audit Board #1
3,139,,,0.051692007,N,Audit Board #1
3,154,,,0.066155011,N,Audit Board #1
3,167,,,0.065394512,N,Audit Board #1
3,171,,,0.042219491,N,Audit Board #1
3,176,,,"0.005218780,0.062366878",N,Audit Board #1
4,2,,,0.076443972,N,Audit Board #1
4,17,,,0.053430602,N,Audit Board #1
4,23,,,0.058163275,N,Audit Board #1
4,24,,,0.016410407,N,Audit Board #1
4,25,,,0.045120258,N,Audit Board #1
4,37,,,0.007555011,N,Audit Board #1
4,54,,,0.010756792,N,Audit Board #1
4,92,,,0.084574975,N,Audit Board #1
4,95,,,0.016333584,N,Audit Board #1
4,113,,,0.019848217,N,Audit Board #1
4,129,,,0.080770854,N,Audit Board #1
4,140,,,0.037883280,N,Audit Board #1
4,143,,,0.084166260,N,Audit Board #1
4,168,,,0.012561523,N,Audit Board #1
4,178,,,0.045506493,N,Audit Board #1
4,184,,,0.057328736,N,Audit Board #1
4,185,,,0.069581494,N,Audit Board #1
4,197,,,0.079527855,N,Audit Board #1
4,207,,,0.020193556,N,Audit Board #1
4,211,,,0.080732090,N,Audit Board #1
7,41,,,0.049935000,N,Audit Board #1
7,47,,,0.044928127,N,Audit Board #1
7,66,,,0.071449550,N,Audit Board #1
7,90,,,0.014480890,N,Audit Board #1
7,97,,,0.000422869,N,Audit Board #1
9,35,,,0.028575144,N,Audit Board #1
9,58,,,0.002239414,N,Audit Board #1
9,60,,,0.088417429,N,Audit Board #1
9,65,,,0.090058075,N,Audit Board #1
9,66,,,0.057133697,N,Audit Board #1
9,75,,,0.005940305,N,Audit Board #1
9,76,,,0.029571656,N,Audit Board #1
9,78,,,0.066056290,N,Audit Board #1
9,82,,,0.030169029,N,Audit Board #1
9,87,,,0.069204096,N,Audit Board #1
9,92,,,0.085740008,N,Audit Board #1
9,103,,,0.017479124,N,Audit Board #1
9,117,,,"0.015073755,0.071754522",N,Audit Board #1
9,120,,,0.069733078,N,Audit Board #1
9,125,,,0.083435111,N,Audit Board #1
9,162,,,0.039105574,N,Audit Board #1
9,167,,,0.076572401,N,Audit Board #1
9,170,,,0.012659967,N,Audit Board #1
9,176,,,0.062920812,N,Audit Board #1
9,178,,,0.015431261,N,Audit Board #1
9,190,,,"0.024942634,0.079568029",N,Audit Board #1
9,205,,,0.004264784,N,Audit Board #1
9,209,,,0.005931925,N,Audit Board #1
9,212,,,"0.014676518,0.029965115",N,Audit Board #1
9,226,,,0.019478257,N,Audit Board #1
9,234,,,0.046644312,N,Audit Board #1
9,235,,,0.075769723,N,Audit Board #1
9,242,,,0.048115489,N,Audit Board #1
9,247,,,0.052251771,N,Audit Board #1
9,251,,,0.080571724,N,Audit Board #1
9,254,,,0.012372409,N,Audit Board #1
9,267,,,0.072672862,N,Audit Board #1
9,280,,,"0.059641462,0.068303669",N,Audit Board #1
9,301,,,0.037462230,N,Audit Board #1
9,322,,,0.040875653,N,Audit Board #1
9,331,,,0.051824848,N,Audit Board #1
9,336,,,0.033869904,N,Audit Board #1
9,342,,,0.041430648,N,Audit Board #1
1,30,,,0.045974803,N,Audit Board #2
1,31,,,0.038473761,N,Audit Board #2
1,42,,,0.072832088,N,Audit Board #2
1,56,,,0.084692321,N,Audit Board #2
1,76,,,0.063689709,N,Audit Board #2
1,77,,,0.010145703,N,Audit Board #2
1,82,,,0.032182577,N,Audit Board #2
1,93,,,0.084948011,N,Audit Board #2
1,112,,,"0.052151395,0.087001115",N,Audit Board #2
10,1,,,0.089705570,N,Audit Board #2
10,2,,,"0.020726848,0.027898446",N,Audit Board #2
10,5,,,0.047704244,N,Audit Board #2
10,7,,,0.055660096,N,Audit Board #2
10,12,,,0.003443858,N,Audit Board #2
10,29,,,0.000726523,N,Audit Board #2
10,30,,,0.079256862,N,Audit Board #2
10,34,,,0.060791594,N,Audit Board #2
10,35,,,0.086814255,N,Audit Board #2
10,40,,,0.080386954,N,Audit Board #2
10,74,,,0.013515621,N,Audit Board #2
10,90,,,0.090325155,N,Audit Board #2
10,91,,,0.039259384,N,Audit Board #2
10,92,,,0.013590837,N,Audit Board #2
10,93,,,0.047499469,N,Audit Board #2
10,96,,,0.090307143,N,Audit Board #2
10,117,,,0.066016716,N,Audit Board #2
10,124,,,0.080206960,N,Audit Board #2
10,129,,,0.005236262,N,Audit Board #2
10,131,,,0.006775266,N,Audit Board #2
10,132,,,0.051803233,N,Audit Board #2
10,134,,,0.072783454,N,Audit Board #2
5,1,,,"0.019890960,0.037375799",N,Audit Board #2
5,4,,,0.017286147,N,Audit Board #2
5,29,,,0.083884961,N,Audit Board #2
5,42,,,0.042686157,N,Audit Board #2
5,48,,,0.032096687,N,Audit Board #2
5,52,,,0.075230157,N,Audit Board #2
5,107,,,0.087737805,N,Audit Board #2
5,114,,,0.029273110,N,Audit Board #2
5,126,,,0.088016505,N,Audit Board #2
5,130,,,0.027832667,N,Audit Board #2
5,135,,,0.062796685,N,Audit Board #2
5,140,,,0.040076077,N,Audit Board #2
5,144,,,"0.014154461,0.084556427",N,Audit Board #2
5,159,,,0.046562710,N,Audit Board #2
5,172,,,0.007517245,N,Audit Board #2
5,173,,,0.066622473,N,Audit Board #2
5,196,,,0.019789300,N,Audit Board #2
5,199,,,0.084429098,N,Audit Board #2
5,204,,,0.032735829,N,Audit Board #2
5,205,,,0.077127168,N,Audit Board #2
5,217,,,0.015325614,N,Audit Board #2
5,222,,,0.073088368,N,Audit Board #2
5,226,,,0.069858216,N,Audit Board #2
6,20,,,0.052650502,N,Audit Board #2
6,23,,,0.024198267,N,Audit Board #2
6,31,,,0.072938796,N,Audit Board #2
6,41,,,"0.067409828,0.091892223",N,Audit Board #2
6,43,,,0.012027652,N,Audit Board #2
6,49,,,0.074713122,N,Audit Board #2
6,70,,,0.077927256,N,Audit Board #2
6,78,,,"0.038840716,0.087754405",N,Audit Board #2
6,102,,,0.032103353,N,Audit Board #2
6,110,,,0.082473117,N,Audit Board #2
6,129,,,0.049479743,N,Audit Board #2
6,143,,,"0.034894131,0.071689460",N,Audit Board #2
6,149,,,0.067361541,N,Audit Board #2
6,153,,,0.028243492,N,Audit Board #2
6,156,,,0.026297323,N,Audit Board #2
6,160,,,0.014968337,N,Audit Board #2
6,179,,,0.065049637,N,Audit Board #2
6,190,,,0.091419854,N,Audit Board #2
6,191,,,0.037080703,N,Audit Board #2
6,227,,,0.065533892,N,Audit Board #2
8,17,,,0.044945281,N,Audit Board #2
8,19,,,0.046824012,N,Audit Board #2
8,64,,,0.014952599,N,Audit Board #2
8,77,,,0.000596883,N,Audit Board #2
8,92,,,0.044046349,N,Audit Board #2
8,99,,,0.002470756,N,Audit Board #2
8,100,,,0.068258005,N,Audit Board #2
8,101,,,0.003431389,N,Audit Board #2
8,103,,,0.058871731,N,Audit Board #2
8,122,,,0.010449387,N,Audit Board #2
8,123,,,0.039266047,N,Audit Board #2
8,128,,,0.024233409,N,Audit Board #2
8,142,,,0.007791157,N,Audit Board #2
8,145,,,0.075594743,N,Audit Board #2
8,146,,,0.058001600,N,Audit Board #2
8,148,,,0.085586631,N,Audit Board #2
8,154,,,0.010169084,N,Audit Board #2
8,162,,,0.000720431,N,Audit Board #2
8,185,,,0.024705314,N,Audit Board #2
8,186,,,0.028614188,N,Audit Board #2
8,194,,,0.038254919,N,Audit Board #2
8,199,,,0.069147874,N,Audit Board #2
8,201,,,0.066170042,N,Audit Board #2
8,204,,,0.047179026,N,Audit Board #2
8,206,,,0.082495574,N,Audit Board #2
8,214,,,0.064418758,N,Audit Board #2
8,227,,,0.072016687,N,Audit Board #2
8,230,,,0.027675301,N,Audit Board #2
"""
