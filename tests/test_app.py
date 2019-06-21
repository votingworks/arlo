import os, math
import tempfile
import json

import pytest

import app

manifest_file_path = os.path.join(os.path.dirname(__file__), "manifest.csv")
small_manifest_file_path = os.path.join(os.path.dirname(__file__), "small-manifest.csv")

def post_json(client, url, obj):
    return client.post(url, headers = {
        'Content-Type' : 'application/json'
    }, data = json.dumps(obj))

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + db_path
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        app.init_db()

    yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_index(client):
    rv = client.get('/')
    assert b'React App' in rv.data

def test_whole_audit_flow(client):
    rv = post_json(
        client, '/audit/basic',
        {
            "name" : "Primary 2019",
            "riskLimit" : 10,
            "randomSeed": "1234567890987654321",

            "contests" : [
                {
                    "id": "contest-1",
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": "candidate-1",
                            "name": "Candidate 1",
                            "numVotes": 48121
                        },
                        {
                            "id": "candidate-2",
                            "name": "Candidate 2",
                            "numVotes": 38026
                        }                        
                    ],

                    "totalBallotsCast": 86147
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    rv = client.get('/audit/status')
    status = json.loads(rv.data)

    assert status["randomSeed"] == "1234567890987654321"
    assert len(status["contests"]) == 1
    assert status["riskLimit"] == 10
    assert status["name"] == "Primary 2019"

    rv = post_json(
        client, '/audit/jurisdictions',
        {
	    "jurisdictions": [
		{
		    "id": "adams-county",
		    "name": "Adams County",
		    "contests": ["contest-1"],
                    "auditBoards": [
			{
			    "id": "audit-board-1",
			    "members": []
			},
			{
			    "id": "audit-board-2",
			    "members": []
			}
		    ]
		}
	    ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "Adams County"
    assert jurisdiction["auditBoards"][1]["id"] == "audit-board-2"
    assert jurisdiction["contests"] == ["contest-1"]

    # upload the manifest
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '/jurisdiction/adams-county/manifest', data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'manifest.csv'
    assert manifest['numBallots'] == 86147
    assert manifest['numBatches'] == 484
    assert manifest['uploadedAt']

    # delete the manifest and make sure that works
    rv = client.delete('/jurisdiction/adams-county/manifest')
    assert json.loads(rv.data)['status'] == "ok"

    rv = client.get('/audit/status')
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']

    assert manifest['filename'] is None
    assert manifest['uploadedAt'] is None

    # upload the manifest again
    data = {}
    data['manifest'] = (open(manifest_file_path, "rb"), 'manifest.csv')
    rv = client.post(
        '/jurisdiction/adams-county/manifest', data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    
    # get the retrieval list for round 1
    rv = client.get('/jurisdiction/adams-county/1/retrieval-list')
    lines = rv.data.decode('utf-8').split("\r\n")
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])

    # post results for round 1
    num_for_winner = int(num_ballots * 0.56)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(client, '/jurisdiction/adams-county/1/results',
                   {
	               "contests": [
		           {
			       "id": "contest-1",
   			       "results": {
				   "candidate-1": num_for_winner,
				   "candidate-2": num_for_loser
			       }
		           }
	               ]
                   })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == "contest-1"
    assert round_contest["results"]["candidate-1"] == num_for_winner
    assert round_contest["results"]["candidate-2"] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 5

@pytest.mark.quick
def test_small_election(client):
    rv = post_json(
        client, '/audit/basic',
        {
            "name" : "Small Test 2019",
            "riskLimit" : 10,
            "randomSeed": "a1234567890987654321b",

            "contests" : [
                {
                    "id": "contest-1",
                    "name": "Contest 1",
                    "choices": [
                        {
                            "id": "candidate-1",
                            "name": "Candidate 1",
                            "numVotes": 1325
                        },
                        {
                            "id": "candidate-2",
                            "name": "Candidate 2",
                            "numVotes": 792
                        }                        
                    ],

                    "totalBallotsCast": 2123
                }
            ]
        })
    
    assert json.loads(rv.data)['status'] == "ok"

    rv = client.get('/audit/status')
    status = json.loads(rv.data)

    assert status["name"] == "Small Test 2019"

    rv = post_json(
        client, '/audit/jurisdictions',
        {
	    "jurisdictions": [
		{
		    "id": "county-1",
		    "name": "County 1",
		    "contests": ["contest-1"],
                    "auditBoards": [
			{
			    "id": "audit-board-1",
			    "members": []
			},
			{
			    "id": "audit-board-2",
			    "members": []
			}
		    ]
		}
	    ]
        })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)

    assert len(status["jurisdictions"]) == 1
    jurisdiction = status["jurisdictions"][0]
    assert jurisdiction["name"] == "County 1"
    assert jurisdiction["auditBoards"][1]["id"] == "audit-board-2"
    assert jurisdiction["contests"] == ["contest-1"]

    # upload the manifest
    data = {}
    data['manifest'] = (open(small_manifest_file_path, "rb"), 'small-manifest.csv')
    rv = client.post(
        '/jurisdiction/county-1/manifest', data=data,
        content_type='multipart/form-data')

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)
    manifest = status['jurisdictions'][0]['ballotManifest']
    
    assert manifest['filename'] == 'small-manifest.csv'
    assert manifest['numBallots'] == 2117
    assert manifest['numBatches'] == 10
    assert manifest['uploadedAt']

    # get the retrieval list for round 1
    rv = client.get('/jurisdiction/county-1/1/retrieval-list')
    lines = rv.data.decode('utf-8').split("\r\n")
    assert lines[0] == "Batch Name,Ballot Number,Storage Location,Tabulator,Times Selected,Audit Board"
    assert 'attachment' in rv.headers['Content-Disposition']

    num_ballots = sum([int(line.split(",")[4]) for line in lines[1:] if line!=""])

    # post results for round 1
    num_for_winner = int(num_ballots * 0.61)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(client, '/jurisdiction/county-1/1/results',
                   {
	               "contests": [
		           {
			       "id": "contest-1",
   			       "results": {
				   "candidate-1": num_for_winner,
				   "candidate-2": num_for_loser
			       }
		           }
	               ]
                   })

    assert json.loads(rv.data)['status'] == 'ok'

    rv = client.get('/audit/status')
    status = json.loads(rv.data)
    round_contest = status["rounds"][0]["contests"][0]
    assert round_contest["id"] == "contest-1"
    assert round_contest["results"]["candidate-1"] == num_for_winner
    assert round_contest["results"]["candidate-2"] == num_for_loser
    assert round_contest["endMeasurements"]["isComplete"]
    assert math.floor(round_contest["endMeasurements"]["pvalue"] * 100) <= 9

