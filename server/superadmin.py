from flask import render_template, redirect, request, Blueprint

from .models import *  # pylint: disable=wildcard-import
from .auth import (
    UserType,
    with_superadmin_access,
    set_loggedin_user,
)

superadmin = Blueprint("superadmin", __name__)


@superadmin.route(
    "/superadmin/", methods=["GET"],
)
@with_superadmin_access
def superadmin_organizations():
    organizations = Organization.query.execution_options(
        query_across_elections=True
    ).all()
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
