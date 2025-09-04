from flask import Blueprint

from .auth_helpers import *

auth = Blueprint("auth", __name__, template_folder=".")


from . import auth_routes  # noqa: E402, F401
