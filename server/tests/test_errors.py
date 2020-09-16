import io
import json
import threading
import logging
from flask.testing import FlaskClient

from ..app import app
from ..bgcompute import (
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
    client: FlaskClient, election_id: str, caplog
):
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    (
                        "Jurisdiction,Admin Email\n"
                        + "\n".join(f"J{i},ja{i}@example.com" for i in range(100))
                    ).encode()
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # We'll delete the election out from under bgcompute to cause it to error
    def delete_election():
        election = Election.query.get(election_id)
        db_session.delete(election)
        db_session.commit()

    thread1 = threading.Thread(target=bgcompute_update_election_jurisdictions_file)
    thread2 = threading.Thread(target=delete_election)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    assert (
        "server.app",
        logging.INFO,
        f"START updating jurisdictions file. election_id: {election_id}",
    ) in caplog.record_tuples
    assert (
        "server.app",
        logging.ERROR,
        f"ERROR updating jurisdictions file. election_id: {election_id}",
    ) in caplog.record_tuples


def test_bgcompute_ballot_manifest_errors(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str], caplog
):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, user_key=DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    (
                        "Batch Name,Number of Ballots\n"
                        + "\n".join(f"B{i},{i}" for i in range(100))
                    ).encode()
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # We'll delete the election out from under bgcompute to cause it to error
    def delete_election():
        election = Election.query.get(election_id)
        db_session.delete(election)
        db_session.commit()

    thread1 = threading.Thread(target=bgcompute_update_ballot_manifest_file)
    thread2 = threading.Thread(target=delete_election)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    assert (
        "server.app",
        logging.INFO,
        f"START updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    ) in caplog.record_tuples
    assert (
        "server.app",
        logging.ERROR,
        f"ERROR updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    ) in caplog.record_tuples


def test_bgcompute_batch_tallies_errors(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    caplog,
):
    election = Election.query.get(election_id)
    election.audit_type = AuditType.BATCH_COMPARISON
    contest_2 = Contest.query.get(contest_ids[1])
    db_session.delete(contest_2)
    db_session.commit()

    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, user_key=DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    (
                        "Batch Name,Number of Ballots\n"
                        + "\n".join(f"B{i},{i}" for i in range(100))
                    ).encode()
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file()
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(
                    (
                        "Batch Name,candidate 1,candidate 2\n"
                        + "\n".join(f"B{i},0,0" for i in range(100))
                    ).encode()
                ),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)

    # We'll delete the jurisdiction out from under bgcompute to cause it to error
    def delete_jurisdiction():
        jurisdiction = Jurisdiction.query.get(jurisdiction_ids[0])
        db_session.delete(jurisdiction)
        db_session.commit()

    thread1 = threading.Thread(target=bgcompute_update_batch_tallies_file)
    thread2 = threading.Thread(target=delete_jurisdiction)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    assert (
        "server.app",
        logging.INFO,
        f"START updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    ) in caplog.record_tuples
    assert (
        "server.app",
        logging.ERROR,
        f"ERROR updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_ids[0]}",
    ) in caplog.record_tuples
