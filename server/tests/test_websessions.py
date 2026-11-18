import time
from datetime import timedelta, timezone, datetime
from unittest.mock import Mock, MagicMock

from ..websession import ArloSessionInterface, cleanup_sessions
from ..models import WebSession
from .. import config
from ..database import db_session


def mock_app_request_response():
    app = Mock()
    app.config = {
        "SESSION_COOKIE_NAME": "COOKIE_MONSTER",
        "SESSION_COOKIE_DOMAIN": "cookie_domain",
        "SESSION_COOKIE_PATH": "/",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SECURE": True,
    }

    req = Mock()
    req.cookies = Mock()
    req.cookies.get = MagicMock(return_value=None)

    resp = Mock()
    resp.set_cookie = MagicMock()

    return app, req, resp


def test_websession_create():
    app, req, resp = mock_app_request_response()
    asi = ArloSessionInterface()
    session = asi.open_session(app, req)
    assert session
    assert session.sid

    req.cookies.get = MagicMock(return_value=session.sid)

    # not yet stored
    assert asi.open_session(app, req).sid != session.sid

    asi.save_session(app, session, resp)

    # not yet in the database cause nothing in the session
    assert asi.open_session(app, req).sid != session.sid

    session["foo"] = "bar"
    asi.save_session(app, session, resp)

    # now in database
    reread_session = asi.open_session(app, req)
    assert reread_session.sid == session.sid
    assert reread_session["foo"] == "bar"

    # artificially set the updated_at time in the past so we can test cleanup
    session_in_db = WebSession.query.filter_by(id=session.sid).first()
    session_in_db.updated_at = (
        datetime.now(timezone.utc)
        - config.SESSION_INACTIVITY_TIMEOUT
        + timedelta(seconds=1)
    )
    db_session.commit()

    # cleanup shouldn't remove the session because 1s hasn't yet elapsed
    cleanup_sessions(db_session)
    session_2 = asi.open_session(app, req)
    assert session_2.sid == session.sid
    assert session_2["foo"] == "bar"

    time.sleep(1)

    # now cleanup should remove the session because 1s has elapsed
    cleanup_sessions(db_session)
    session_3 = asi.open_session(app, req)
    assert session_3.sid != session.sid
    assert "foo" not in session_3


def saved_session(initial):  # noqa: ANN001
    app, req, resp = mock_app_request_response()
    asi = ArloSessionInterface()
    session = asi.open_session(app, req)
    session.update(initial)
    asi.save_session(app, session, resp)
    req.cookies.get = MagicMock(return_value=session.sid)
    return (
        lambda: asi.open_session(app, req),
        lambda session: asi.save_session(app, session, resp),
    )


def test_websession_overlapping_requests_keep_each_others_changes():
    open_request, save = saved_session({"user": None, "last_request_at": 1})
    slow_request, login_request = open_request(), open_request()

    login_request["user"] = "jurisdiction_admin"
    save(login_request)
    slow_request["last_request_at"] = 2
    save(slow_request)

    assert dict(open_request()) == {
        "_permanent": True,
        "user": "jurisdiction_admin",
        "last_request_at": 2,
    }


def test_websession_overlapping_requests_keep_each_others_deletions():
    open_request, save = saved_session({"oauth_state": "abc"})
    callback_request, other_request = open_request(), open_request()

    del callback_request["oauth_state"]
    save(callback_request)
    other_request["user"] = "audit_admin"
    save(other_request)

    assert dict(open_request()) == {"_permanent": True, "user": "audit_admin"}


def test_websession_setting_a_key_to_its_loaded_value_still_writes_it():
    open_request, save = saved_session({"user": None})
    login_request, logout_request = open_request(), open_request()

    login_request["user"] = "jurisdiction_admin"
    save(login_request)
    logout_request["user"] = None
    save(logout_request)

    assert dict(open_request()) == {"_permanent": True, "user": None}
