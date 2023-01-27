import time
from datetime import timedelta, timezone, datetime
from unittest.mock import Mock, MagicMock

from ..websession import ArloSessionInterface, cleanup_sessions
from ..models import WebSession
from .. import config
from ..database import db_session


def test_websession_create():
    app = Mock()
    app.session_cookie_name = "COOKIE_MONSTER"
    app.config = {
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
    cleanup_sessions()
    session_2 = asi.open_session(app, req)
    assert session_2.sid == session.sid
    assert session_2["foo"] == "bar"

    time.sleep(1)

    # now cleanup should remove the session because 1s has elapsed
    cleanup_sessions()
    session_3 = asi.open_session(app, req)
    assert session_3.sid != session.sid
    assert "foo" not in session_3
