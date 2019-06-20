import os
import tempfile
import json

import pytest

import app

manifest_file_path = os.path.join(os.path.dirname(__file__), "manifest.csv")

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
                            "numVotes": 42
                        },
                        {
                            "id": "candidate-2",
                            "name": "Candidate 2",
                            "numVotes": 19
                        }                        
                    ],

                    "totalBallotsCast": 85
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

