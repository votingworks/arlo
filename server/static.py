import os
from flask import send_from_directory, render_template

from .config import STATIC_FOLDER, FLASK_ENV, SENTRY_DSN
from .app import app

# Serve the React App at remaining URLs that aren't static files
@app.route("/")
@app.route("/<path:path>")
def serve(path="index.html"):
    if path != "index.html" and os.path.exists(os.path.join(STATIC_FOLDER, path)):
        return send_from_directory(STATIC_FOLDER, path)
    return render_template(
        "index.html", flask_env=FLASK_ENV, sentry_dsn=SENTRY_DSN or ""
    )
