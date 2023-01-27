from urllib.parse import urlparse
from flask import Flask
from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from werkzeug.wrappers import Request
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import (
    FLASK_ENV,
    HTTP_ORIGIN,
    STATIC_FOLDER,
)
from .database import init_db, db_session, engine
from .api import api
from .auth import auth
from .auth.auth_routes import oauth
from .sentry import configure_sentry
from .websession import ArloSessionInterface

if FLASK_ENV not in ["development", "test"]:
    # Restrict which hosts we trust when not in dev/test. This works by causing
    # anything accessing the request URL (i.e. `request.url` or similar) to
    # throw an exception if it doesn't match one of the values in this list.
    Request.trusted_hosts = [str(urlparse(HTTP_ORIGIN).hostname)]  # pragma: no cover

app = Flask("arlo", static_folder=None, template_folder=STATIC_FOLDER)
app.wsgi_app = ProxyFix(app.wsgi_app)  # type: ignore
app.testing = FLASK_ENV == "test"
Talisman(
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
csrf = SeaSurf(app)

init_db()

app.session_interface = ArloSessionInterface()

oauth.init_app(app)

app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(auth)

# pylint: disable=wrong-import-position,cyclic-import,unused-import
from . import static
from . import errors


@app.teardown_appcontext
def shutdown_session(exception=None):  # pylint: disable=unused-argument
    db_session.remove()


# Ensure that every endpoint has an access control decorator
for rule in app.url_map.iter_rules():
    if not hasattr(app.view_functions[rule.endpoint], "has_access_control"):
        raise Exception(
            f"Missing access control decorator for {rule.endpoint}"
        )  # pragma: no cover


configure_sentry(app)


# Dispose the database engine after we're finished with app setup. (A new
# connection will be created when requests start coming in.) This ensures that
# when we run the server in multiple processes (e.g. with gunicorn), we can
# fork those processes after loading the app (e.g. with gunicorn --preload)
# without having two copies of the same database connection, which causes
# errors. See https://stackoverflow.com/questions/22752521/uwsgi-flask-sqlalchemy-and-postgres-ssl-error-decryption-failed-or-bad-reco.
engine.dispose()
