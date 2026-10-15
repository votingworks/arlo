from flask.testing import FlaskClient


def test_index(client: FlaskClient):
    rv = client.get("/")
    assert b"Arlo, by VotingWorks" in rv.data

    rv = client.get("/election/1234")
    assert b"Arlo, by VotingWorks" in rv.data

    rv = client.get("/election/1234/audit-board/5677")
    assert b"Arlo, by VotingWorks" in rv.data


def test_logo(client: FlaskClient):
    rv = client.get("/public/votingworks-logo.png")
    assert b"\211PNG" in rv.data


def test_static_logo(client: FlaskClient):
    rv = client.get("/votingworks-logo.png")
    assert rv.status_code == 200


def test_content_security_policy(client: FlaskClient):
    rv = client.get("/")
    directives = dict(
        directive.strip().split(" ", 1)
        for directive in rv.headers["Content-Security-Policy"].split(";")
    )
    assert directives["script-src"] == "'self'"
