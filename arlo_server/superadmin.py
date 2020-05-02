from flask import render_template, redirect, request

from arlo_server import app
from arlo_server.models import Organization, Election
from arlo_server.auth import (
    UserType,
    with_superadmin_access,
    set_loggedin_user,
)


@app.route(
    "/superadmin/", methods=["GET"],
)
@with_superadmin_access
def superadmin_organizations():
    organizations = Organization.query.all()
    return render_template("superadmin/organizations.html", organizations=organizations)


@app.route(
    "/superadmin/jurisdictions", methods=["GET"],
)
@with_superadmin_access
def superadmin_jurisdictions():
    election_id = request.args["election_id"]
    election = Election.query.filter_by(id=election_id).one()
    return render_template("superadmin/jurisdictions.html", election=election)


@app.route(
    "/superadmin/auditadmin-login", methods=["POST"],
)
@with_superadmin_access
def superadmin_auditadmin_login():
    user_email = request.form["email"]
    set_loggedin_user(UserType.AUDIT_ADMIN, user_email)
    return redirect("/")


@app.route(
    "/superadmin/jurisdictionadmin-login", methods=["POST"],
)
@with_superadmin_access
def superadmin_jurisdictionadmin_login():
    user_email = request.form["email"]
    set_loggedin_user(UserType.JURISDICTION_ADMIN, user_email)
    return redirect("/")
