import uuid
from flask import render_template, redirect, request

from arlo_server import app, db
from arlo_server.models import *
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
    organizations = Organization.query.all()
    election_id = request.args["election_id"]
    election = Election.query.filter_by(id=election_id).one()
    return render_template(
        "superadmin/jurisdictions.html", election=election, organizations=organizations
    )


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


def new_id():
    return str(uuid.uuid4())


def clone_user_with_prefix(user, prefix):
    prefix = prefix.lower()
    if user.email.startswith(prefix):
        return user

    new_email = f"{prefix}{user.email}"
    new_user = User.query.filter_by(email=new_email).one_or_none()

    if not new_user:
        new_user = User(id=new_id(), email=new_email)
        db.session.add(new_user)

    return new_user


@app.route("/superadmin/election-clone", methods=["POST"])
@with_superadmin_access
def superadmin_election_clone():
    election_id = request.form["election_id"]
    organization_id = request.form["organization_id"]
    name = request.form["name"]

    old_election = Election.query.filter_by(id=election_id).one()

    new_election = Election(
        id=new_id(),
        organization_id=organization_id,
        audit_name=name,
        election_name=old_election.election_name,
        state=old_election.state,
        election_date=old_election.election_date,
        election_type=old_election.election_type,
        meeting_date=old_election.meeting_date,
        risk_limit=old_election.risk_limit,
        random_seed=old_election.random_seed,
        online=old_election.online,
        is_multi_jurisdiction=old_election.is_multi_jurisdiction,
        frozen_at=old_election.frozen_at,
    )

    if old_election.jurisdictions_file_id:
        old_file = old_election.jurisdictions_file
        new_file = File(
            id=new_id(),
            name=old_file.name,
            contents=old_file.contents,
            uploaded_at=old_file.uploaded_at,
            processing_started_at=old_file.processing_started_at,
            processing_completed_at=old_file.processing_completed_at,
            processing_error=old_file.processing_error,
        )
        db.session.add(new_file)

        new_election.jurisdictions_file_id = new_file.id

    db.session.add(new_election)

    round_map = {}

    for old_round in old_election.rounds:
        new_round = Round(
            id=new_id(),
            election_id=new_election.id,
            round_num=old_round.round_num,
            ended_at=old_round.ended_at,
        )

        round_map[old_round.id] = new_round

        db.session.add(new_round)

    contest_map = {}
    choice_map = {}

    for old_contest in old_election.contests:
        new_contest = Contest(
            id=new_id(),
            election_id=new_election.id,
            name=old_contest.name,
            is_targeted=old_contest.is_targeted,
            total_ballots_cast=old_contest.total_ballots_cast,
            num_winners=old_contest.num_winners,
            votes_allowed=old_contest.votes_allowed,
        )

        # this map keeps the old object around because it's needed
        contest_map[old_contest.id] = (old_contest, new_contest)

        db.session.add(new_contest)

        for old_choice in old_contest.choices:
            new_choice = ContestChoice(
                id=new_id(),
                contest_id=new_contest.id,
                name=old_choice.name,
                num_votes=old_choice.num_votes,
            )

            choice_map[old_choice.id] = new_choice

            db.session.add(new_choice)

        for old_roundcontest in RoundContest.query.filter_by(contest_id=old_contest.id):
            new_roundcontest = RoundContest(
                round_id=round_map[old_roundcontest.round_id].id,
                contest_id=new_contest.id,
                sample_size_options=old_roundcontest.sample_size_options,
                end_p_value=old_roundcontest.end_p_value,
                is_complete=old_roundcontest.is_complete,
                sample_size=old_roundcontest.sample_size,
            )

            db.session.add(new_roundcontest)

            for old_result in old_roundcontest.results:
                new_result = RoundContestResult(
                    round_id=round_map[old_result.round_id].id,
                    contest_id=new_contest.id,
                    contest_choice_id=choice_map[old_result.contest_choice_id].id,
                    result=old_result.result,
                )
                db.session.add(new_result)

    jurisdiction_map = {}

    for old_jurisdiction in old_election.jurisdictions:
        new_jurisdiction = Jurisdiction(
            id=new_id(),
            election_id=new_election.id,
            name=old_jurisdiction.name,
            manifest_num_ballots=old_jurisdiction.manifest_num_ballots,
            manifest_num_batches=old_jurisdiction.manifest_num_batches,
        )

        jurisdiction_map[old_jurisdiction.id] = new_jurisdiction

        if old_jurisdiction.manifest_file_id:
            old_file = old_jurisdiction.manifest_file
            new_file = File(
                id=new_id(),
                name=old_file.name,
                contents=old_file.contents,
                uploaded_at=old_file.uploaded_at,
                processing_started_at=old_file.processing_started_at,
                processing_completed_at=old_file.processing_completed_at,
                processing_error=old_file.processing_error,
            )
            db.session.add(new_file)

            new_jurisdiction.manifest_file_id = new_file.id

        db.session.add(new_jurisdiction)

        for old_ja in old_jurisdiction.jurisdiction_administrations:
            new_user = clone_user_with_prefix(old_ja.user, "superadmin--")
            new_ja = JurisdictionAdministration(
                user_id=new_user.id, jurisdiction_id=new_jurisdiction.id
            )
            db.session.add(new_ja)

        ab_map = {}

        for old_auditboard in old_jurisdiction.audit_boards:
            new_auditboard = AuditBoard(
                id=new_id(),
                jurisdiction_id=new_jurisdiction.id,
                round_id=round_map[old_auditboard.round_id].id,
                name=old_auditboard.name,
                member_1=old_auditboard.member_1,
                member_1_affiliation=old_auditboard.member_1_affiliation,
                member_2=old_auditboard.member_2,
                member_2_affiliation=old_auditboard.member_2_affiliation,
                passphrase=new_id(),
                signed_off_at=old_auditboard.signed_off_at,
            )

            ab_map[old_auditboard.id] = new_auditboard

            db.session.add(new_auditboard)

        for old_batch in old_jurisdiction.batches:
            new_batch = Batch(
                id=new_id(),
                jurisdiction_id=new_jurisdiction.id,
                name=old_batch.name,
                num_ballots=old_batch.num_ballots,
                storage_location=old_batch.storage_location,
                tabulator=old_batch.tabulator,
            )
            db.session.add(new_batch)

            for old_ballot in old_batch.ballots:
                new_ballot = SampledBallot(
                    id=new_id(),
                    batch_id=new_batch.id,
                    ballot_position=old_ballot.ballot_position,
                    status=old_ballot.status,
                )
                if old_ballot.audit_board_id:
                    new_ballot.audit_board_id = ab_map[old_ballot.audit_board_id].id

                db.session.add(new_ballot)

                for old_draw in old_ballot.draws:
                    new_draw = SampledBallotDraw(
                        ballot_id=new_ballot.id,
                        round_id=round_map[old_draw.round_id].id,
                        ticket_number=old_draw.ticket_number,
                    )
                    db.session.add(new_draw)

                for old_interpretation in old_ballot.interpretations:
                    new_interpretation = BallotInterpretation(
                        ballot_id=new_ballot.id,
                        contest_id=contest_map[old_interpretation.contest_id][1].id,
                        interpretation=old_interpretation.interpretation,
                        comment=old_interpretation.comment,
                        contest_choice_id=choice_map[
                            old_interpretation.contest_choice_id
                        ].id,
                    )

    for (old_contest, new_contest) in contest_map.values():
        new_contest.jurisdictions = [
            jurisdiction_map[j.id] for j in old_contest.jurisdictions
        ]

    db.session.commit()
    return redirect("/superadmin/")
