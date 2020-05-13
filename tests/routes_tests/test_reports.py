from flask.testing import FlaskClient


def test_audit_admin_report(
    client: FlaskClient, election_id: str, round_1_id: str, round_2_id: str
):
    rv = client.get(f"/election/{election_id}/report")
    report = rv.data.decode("utf-8")
    print(report)
    assert False
