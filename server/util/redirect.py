from urllib.parse import urljoin
from flask import redirect as flask_redirect
from ..config import HTTP_ORIGIN


# Use the app's configured origin for redirects since the Flask dev server
# origin (localhost:3001) is different from the frontend dev server origin
# (localhost:3000). We always want to user to be redirected to the frontend dev
# server (to avoid CORS issues in Cypress tests, among other reasons).
def redirect(path: str):
    return flask_redirect(urljoin(HTTP_ORIGIN, path))
