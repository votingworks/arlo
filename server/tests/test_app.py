from flask.testing import FlaskClient


def test_index(client: FlaskClient):
    rv = client.get("/")
    assert b"Arlo (by VotingWorks)" in rv.data

    rv = client.get("/election/1234")
    assert b"Arlo (by VotingWorks)" in rv.data

    rv = client.get("/election/1234/audit-board/5677")
    assert b"Arlo (by VotingWorks)" in rv.data


def test_static_logo(client: FlaskClient):
    rv = client.get("/arlo.png")
    assert rv.status_code == 200
