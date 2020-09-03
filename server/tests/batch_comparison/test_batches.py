from typing import List
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import

J1_BATCHES_ROUND_1 = 3


def test_list_batches_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches"
    )
    assert rv.status_code == 404


def test_list_batches_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    assert len(batches) == J1_BATCHES_ROUND_1
    compare_json(
        batches[0],
        {"id": assert_is_id, "name": "Batch 1", "numBallots": 200, "auditBoard": None},
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    batches = json.loads(rv.data)["batches"]
    compare_json(
        batches[0],
        {
            "id": assert_is_id,
            "name": "Batch 1",
            "numBallots": 200,
            "auditBoard": {"id": assert_is_id, "name": "Audit Board #1"},
        },
    )


def test_batch_retrieval_list_bad_round_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/not-a-real-round/batches/retrieval-list"
    )
    assert rv.status_code == 404


def test_batch_retrieval_list_round_1(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,
    snapshot,
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    assert rv.status_code == 200
    assert "attachment; filename=" in rv.headers["Content-Disposition"]
    assert ".csv" in rv.headers["Content-Disposition"]

    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert (
        retrieval_list
        == "Batch Name,Storage Location,Tabulator,Already Audited,Audit Board\n"
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    assert len(retrieval_list.splitlines()) == J1_BATCHES_ROUND_1 + 1
    snapshot.assert_match(retrieval_list)
