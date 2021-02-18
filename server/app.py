from urllib.parse import urlparse
from flask import Flask
from flask_talisman import Talisman
from werkzeug.wrappers import Request
from werkzeug.middleware.proxy_fix import ProxyFix
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from .config import (
    SESSION_SECRET,
    FLASK_ENV,
    DEVELOPMENT_ENVS,
    HTTP_ORIGIN,
    SENTRY_DSN,
    STATIC_FOLDER,
)
from .database import init_db, db_session, engine
from .api import api
from .auth import auth
from .auth.routes import oauth

if FLASK_ENV not in DEVELOPMENT_ENVS:
    # Restrict which hosts we trust when not in dev/test. This works by causing
    # anything accessing the request URL (i.e. `request.url` or similar) to
    # throw an exception if it doesn't match one of the values in this list.
    Request.trusted_hosts = [str(urlparse(HTTP_ORIGIN).hostname)]  # pragma: no cover

app = Flask("arlo", static_folder=None, template_folder=STATIC_FOLDER)
app.wsgi_app = ProxyFix(app.wsgi_app)  # type: ignore
app.testing = FLASK_ENV == "test"
T = Talisman(
    app,
    force_https_permanent=True,
    session_cookie_http_only=True,
    feature_policy="camera 'none'; microphone 'none'; geolocation 'none'",
    # TODO: Configure webpack to use a nonce: https://webpack.js.org/guides/csp/.
    content_security_policy={
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline'",
        "style-src": "'self' 'unsafe-inline'",
    },
)
app.secret_key = SESSION_SECRET

init_db()

oauth.init_app(app)

app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(auth)

# pylint: disable=wrong-import-position,cyclic-import,unused-import
from . import static
from . import errors


@app.teardown_appcontext
def shutdown_session(exception=None):  # pylint: disable=unused-argument
    db_session.remove()


# Configure Sentry to record exceptions
sentry_sdk.init(
    SENTRY_DSN,
    environment=FLASK_ENV,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.2,
)

# Dispose the database engine after we're finished with app setup. (A new
# connection will be created when requests start coming in.) This ensures that
# when we run the server in multiple processes (e.g. with gunicorn), we can
# fork those processes after loading the app (e.g. with gunicorn --preload)
# without having two copies of the same database connection, which causes
# errors. See https://stackoverflow.com/questions/22752521/uwsgi-flask-sqlalchemy-and-postgres-ssl-error-decryption-failed-or-bad-reco.
engine.dispose()
