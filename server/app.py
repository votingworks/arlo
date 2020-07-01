from urllib.parse import urlparse
from flask import Flask
from flask_talisman import Talisman
from werkzeug.wrappers import Request
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import (
    SESSION_SECRET,
    FLASK_ENV,
    DEVELOPMENT_ENVS,
    HTTP_ORIGIN,
)
from .database import init_db, db_session
from .api import api
from .auth import auth
from .auth.routes import oauth
from .superadmin import superadmin

if FLASK_ENV not in DEVELOPMENT_ENVS:
    # Restrict which hosts we trust when not in dev/test. This works by causing
    # anything accessing the request URL (i.e. `request.url` or similar) to
    # throw an exception if it doesn't match one of the values in this list.
    Request.trusted_hosts = [str(urlparse(HTTP_ORIGIN).hostname)]  # pragma: no cover

app = Flask(__name__, static_folder=None)
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
app.register_blueprint(superadmin)

# pylint: disable=wrong-import-position,cyclic-import,unused-import
from . import static
from . import errors


@app.teardown_appcontext
def shutdown_session(exception=None):  # pylint: disable=unused-argument
    db_session.remove()
