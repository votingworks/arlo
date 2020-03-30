from flask import Flask
from flask_talisman import Talisman
from werkzeug.wrappers import Request

from config import (
    STATIC_FOLDER,
    SESSION_SECRET,
    DATABASE_URL,
    FLASK_ENV,
    DEVELOPMENT_ENVS,
    HTTP_ORIGIN,
)
from arlo_server.models import db

if FLASK_ENV not in DEVELOPMENT_ENVS:
    # Restrict which hosts we trust when not in dev/test. This works by causing
    # anything accessing the request URL (i.e. `request.url` or similar) to
    # throw an exception if it doesn't match one of the values in this list.
    Request.trusted_hosts = [HTTP_ORIGIN]

app = Flask(__name__, static_folder=STATIC_FOLDER)
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

# The order of these imports is important as it defines route precedence.
# Be careful when re-ordering them.
import arlo_server.election_settings
import arlo_server.routes
import arlo_server.contests
import arlo_server.jurisdictions
import arlo_server.sample_sizes
import arlo_server.rounds
