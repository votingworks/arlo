# code for this started by copying the bits of flask-session
# https://github.com/mcrowson/flask-sessionstore-fork/blob/master/flask_sessionstore/sessions.py
# that are relevant for database-backed storage, then simplifying for just our use case.

import secrets
from datetime import datetime, timezone

from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from .models import WebSession
from .database import db_session
from . import config


class ArloSession(CallbackDict, SessionMixin):  # pylint: disable=too-many-ancestors
    def __init__(self, sid=None, initial=None):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.permanent = True
        self.modified = False


class ArloSessionInterface(SessionInterface):
    def _generate_sid(self):
        return secrets.token_urlsafe(50)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            return ArloSession(sid=self._generate_sid())

        saved_session = WebSession.query.filter_by(id=sid).first()

        if saved_session:
            return ArloSession(sid=sid, initial=saved_session.data)
        else:
            return ArloSession(sid=self._generate_sid())

    def save_session(self, app, session, response):
        if not session.modified:
            return

        # if the URL handler performed some database updates and then errored out,
        # this method is still being called, and because we are about to update the database
        # for the purposes of updating the session information, we need to be mindful not to
        # mistakenly commit data within our transaction that should have been rolled back.
        # Thus, we call session.remove, which rolls back any un-committed transaction from the URL handler,
        # but has no impact if the URL handler completed successfully and called commit().
        db_session.remove()

        saved_session = WebSession.query.filter_by(id=session.sid).first()

        if saved_session:
            saved_session.data = dict(session)
        else:
            new_session = WebSession(id=session.sid, data=dict(session))
            db_session.add(new_session)

        db_session.commit()

        # expiring the cookie isn't strictly necessary since we kill the session server-side,
        # but it's nice additional hygiene and defense-in-depth.
        #
        # Knowing everything we know about the codebase at this time, where the session
        # is updated on every hit, we could make this age as short as INACTIVITY_TIMEOUT.
        # However, to be resilient to future code changes, we let this cookie live at least
        # as long as the max life of a session, which may prevent hard-to-track bugs in the future
        # where we change how often we save the session to disk.
        max_age = config.SESSION_LIFETIME

        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)

        response.set_cookie(
            app.session_cookie_name,
            session.sid,
            max_age=max_age,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
        )


def cleanup_sessions():
    """
    Because we keep session freshness information in fields embedded inside the data column,
    the only marker in the database that we can safely and cleanly use to clean up a session is the updated_at field.
    """
    query = WebSession.query.filter(
        WebSession.updated_at
        < datetime.now(timezone.utc) - config.SESSION_INACTIVITY_TIMEOUT
    )
    query.delete()
