import io
import json
import logging
from flask.testing import FlaskClient

from ..app import app
from ..worker import bgcompute
from ..worker.bgcompute import (
    bgcompute_update_election_jurisdictions_file,
    bgcompute_update_ballot_manifest_file,
    bgcompute_update_batch_tallies_file,
)
from .helpers import *  # pylint: disable=wildcard-import


def test_uncaught_exception_500(client: FlaskClient):
    # Need to turn this off to hit the error handler (it's turned on
    # automatically in test)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    rv = client.get("/test_uncaught_exception")
    assert rv.status_code == 500
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Internal Server Error", "message": "Catch me if you can!"}
        ]
    }


def test_internal_error_500(client: FlaskClient):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    rv = client.get("/test_internal_error")
    assert rv.status_code == 500
    assert (
        rv.data
        == b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>500 Internal Server Error</title>\n<h1>Internal Server Error</h1>\n<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>\n'
    )


def test_bgcompute_jurisdictions_file_errors(
    client: FlaskClient, election_id: str, caplog, monkeypatch
):
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(("Jurisdiction,Admin Email\n").encode()),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    mock_exception = Exception("mock error")

    def raise_exception(*args):
        raise mock_exception

    monkeypatch.setattr(bgcompute, "process_jurisdictions_file", raise_exception)

    bgcompute_update_election_jurisdictions_file(election_id)

    assert find_log(
        caplog,
        logging.INFO,
        f"START updating jurisdictions file. election_id: {election_id}",
    )
    err_log = find_log(
        caplog,
        logging.ERROR,
        f"ERROR updating jurisdictions file. election_id: {election_id}",
    )
    assert err_log
    assert err_log.exc_info[1] == mock_exception  # type: ignore


def test_bgcompute_ballot_manifest_errors(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    caplog,
    monkeypatch,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, user_key=default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(("Batch Name,Number of Ballots\n").encode()),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    mock_exception = Exception("mock error")

    def raise_exception(*args):
        raise mock_exception

    monkeypatch.setattr(bgcompute, "process_ballot_manifest_file", raise_exception)

    bgcompute_update_ballot_manifest_file(election_id)

    assert find_log(
        caplog,
        logging.INFO,
        f"START updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    )
    err_log = find_log(
        caplog,
        logging.ERROR,
        f"ERROR updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    )
    assert err_log
    assert err_log.exc_info[1] == mock_exception  # type: ignore


def test_bgcompute_batch_tallies_errors(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    caplog,
    monkeypatch,
):
    election = Election.query.get(election_id)
    election.audit_type = AuditType.BATCH_COMPARISON
    election.audit_math_type = AuditMathType.MACRO
    contest_2 = Contest.query.get(contest_ids[1])
    db_session.delete(contest_2)
    db_session.commit()

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, user_key=default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(("Batch Name,candidate 1,candidate 2\n").encode()),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    mock_exception = Exception("mock error")

    def raise_exception(*args):
        raise mock_exception

    monkeypatch.setattr(bgcompute, "process_batch_tallies_file", raise_exception)

    bgcompute_update_batch_tallies_file(election_id)

    assert find_log(
        caplog,
        logging.INFO,
        f"START updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    )
    err_log = find_log(
        caplog,
        logging.ERROR,
        f"ERROR updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    )
    assert err_log
    assert err_log.exc_info[1] == mock_exception  # type: ignore
