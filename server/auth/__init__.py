from flask import Blueprint

from .lib import *

auth = Blueprint("auth", __name__)

# pylint: disable=wrong-import-position,cyclic-import
from . import routes
