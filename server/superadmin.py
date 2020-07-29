from flask import render_template, redirect, request, Blueprint
from werkzeug.exceptions import Forbidden

from .models import *  # pylint: disable=wildcard-import
from .database import db_session
from .auth import (
    UserType,
    with_superadmin_access,
    set_loggedin_user,
)
from .config import FLASK_ENV

superadmin = Blueprint("superadmin", __name__)


@superadmin.route(
    "/superadmin/", methods=["GET"],
)
@with_superadmin_access
def superadmin_organizations():
    organizations = Organization.query.all()
    return render_template("superadmin/organizations.html", organizations=organizations)


@superadmin.route(
    "/superadmin/jurisdictions", methods=["GET"],
)
@with_superadmin_access
def superadmin_jurisdictions():
    election_id = request.args["election_id"]
    election = Election.query.filter_by(id=election_id).one()
    return render_template("superadmin/jurisdictions.html", election=election)


@superadmin.route(
    "/superadmin/auditadmin-login", methods=["POST"],
)
@with_superadmin_access
def superadmin_auditadmin_login():
    user_email = request.form["email"]
    set_loggedin_user(UserType.AUDIT_ADMIN, user_email)
    return redirect("/")


@superadmin.route(
    "/superadmin/jurisdictionadmin-login", methods=["POST"],
)
@with_superadmin_access
def superadmin_jurisdictionadmin_login():
    user_email = request.form["email"]
    set_loggedin_user(UserType.JURISDICTION_ADMIN, user_email)
    return redirect("/")


@superadmin.route("/superadmin/delete-election/<election_id>", methods=["POST"])
@with_superadmin_access
def superadmin_delete_election(election_id: str):
    if FLASK_ENV == "production":  # pragma: no cover
        raise Forbidden("Can't delete audits in production")
    election = get_or_404(Election, election_id)
    db_session.delete(election)
    db_session.commit()
    return redirect("/superadmin/")
