from flask import Blueprint

from .auth_helpers import *

auth = Blueprint("auth", __name__, template_folder=".")

# pylint: disable=wrong-import-position,cyclic-import
from . import auth_routes
