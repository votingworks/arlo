from urllib.parse import urlparse
from flask import Flask
from flask_talisman import Talisman
from werkzeug.wrappers import Request
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import (
    SESSION_SECRET,
    DATABASE_URL,
    FLASK_ENV,
    DEVELOPMENT_ENVS,
    HTTP_ORIGIN,
)
from .models import db

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

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.app = app
db.init_app(app)

# pylint: disable=wrong-import-position,cyclic-import,unused-import

# Authentication
from .api import auth_routes

# Single-jurisdiction flow routes
from .api import routes

# Multi-jurisdiction flow routes
from .api import election_settings
from .api import contests
from .api import jurisdictions
from .api import sample_sizes
from .api import rounds
from .api import audit_boards
from .api import ballots
from .api import reports

# VX superadmin view
from . import superadmin

# Static assets
from . import static

# Error handlers
from . import errors
