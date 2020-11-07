from flask import jsonify

from . import api
from .. import config


@api.route("/config", methods=["GET"])
def config_read():
    return jsonify({"allowAlternateMath": config.ALLOW_ALTERNATE_MATH})
