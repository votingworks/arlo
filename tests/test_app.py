import os
import tempfile
import json

import pytest

import app

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

def test_audit_config(client):
    rv = client.get('/admin/config')
    config = json.loads(rv.data)
    assert config['id'] == 1

    rv = client.post('/admin/config', headers = {
        'Content-Type': 'application/json'
    }, data = json.dumps({
        'name': 'Test Election',
        'jurisdictions': ['A', 'Q', 'F']
    }))

    rv = client.get('/admin/config')
    config = json.loads(rv.data)
    assert config['jurisdictions'] == ['A','Q','F']
    assert config['name'] == 'Test Election'
