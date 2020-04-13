from flask import jsonify, request
import uuid
from datetime import datetime
from typing import List, Dict
from xkcdpass import xkcd_password as xp
from werkzeug.exceptions import Conflict, BadRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_

from arlo_server import app, db
from arlo_server.routes import sample_results
from arlo_server.auth import with_jurisdiction_access, with_audit_board_access
from arlo_server.rounds import get_current_round
from arlo_server.models import (
    AuditBoard,
    Round,
    Election,
    Jurisdiction,
    SampledBallot,
    SampledBallotDraw,
    Batch,
)
from arlo_server.errors import handle_unique_constraint_error
from util.jsonschema import validate, JSONDict
from util.binpacking import BalancedBucketList, Bucket
from util.group_by import group_by
from util.isoformat import isoformat
from audit_math import bravo, sampler_contest

WORDS = xp.generate_wordlist(wordfile=xp.locate_wordfile())

CREATE_AUDIT_BOARD_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"},},
    "additionalProperties": False,
    "required": ["name"],
}

# Raises if invalid
def validate_audit_boards(
    audit_boards: List[JSONDict],
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
):
    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(f"Round {round.round_num} is not the current round")

    if any(ab for ab in jurisdiction.audit_boards if ab.round_id == round.id):
        raise Conflict(f"Audit boards already created for round {round.round_num}")

    validate(
        audit_boards, {"type": "array", "items": CREATE_AUDIT_BOARD_REQUEST_SCHEMA}
    )


def assign_sampled_ballots(
    jurisdiction: Jurisdiction, round: Round, audit_boards: List[AuditBoard],
):
    # Collect the physical ballots for each batch that were sampled for this
    # jurisdiction for this round
    sampled_ballots = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallot.draws)
        .filter_by(round_id=round.id)
        .order_by(SampledBallot.batch_id)  # group_by prefers a sorted list
        .all()
    )
    ballots_by_batch = group_by(sampled_ballots, key=lambda sb: sb.batch_id)

    # Divvy up batches of ballots between the audit boards.
    # Note: BalancedBucketList doesn't care which buckets have which batches to
    # start, so we add all the batches to the first bucket before balancing.
    buckets = [Bucket(audit_board.id) for audit_board in audit_boards]
    for batch_id, sampled_ballots in ballots_by_batch.items():
        buckets[0].add_batch(batch_id, len(sampled_ballots))
    balanced_buckets = BalancedBucketList(buckets)

    for bucket in balanced_buckets.buckets:
        ballots_in_bucket = [
            ballot
            for batch_id in bucket.batches
            for ballot in ballots_by_batch[batch_id]
        ]
        for ballot in ballots_in_bucket:
            ballot.audit_board_id = bucket.name
            db.session.add(ballot)

    db.session.commit()


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board",
    methods=["POST"],
)
@with_jurisdiction_access
def create_audit_boards(election: Election, jurisdiction: Jurisdiction, round_id: str):
    json_audit_boards = request.get_json()
    round = Round.query.get_or_404(round_id)
    validate_audit_boards(json_audit_boards, election, jurisdiction, round)

    audit_boards = [
        AuditBoard(
            id=str(uuid.uuid4()),
            name=json_audit_board["name"],
            jurisdiction_id=jurisdiction.id,
            round_id=round.id,
            passphrase=xp.generate_xkcdpassword(WORDS, numwords=4, delimiter="-"),
        )
        for json_audit_board in json_audit_boards
    ]
    db.session.add_all(audit_boards)

    try:
        db.session.commit()
    except IntegrityError as e:
        handle_unique_constraint_error(
            e,
            constraint_name="audit_board_jurisdiction_id_round_id_name_key",
            message="Audit board names must be unique",
        )

    assign_sampled_ballots(jurisdiction, round, audit_boards)

    return jsonify(status="ok")


def round_status_by_audit_board(
    jurisdiction_id: str, round_id: str
) -> Dict[str, JSONDict]:
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_id, round_id=round_id
    ).all()
    sampled_ballots_by_audit_board = dict(
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(SampledBallot)
        .join(AuditBoard)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .group_by(AuditBoard.id)
        .values(AuditBoard.id, func.count())
    )
    audited_ballots_by_audit_board = dict(
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(SampledBallot)
        .filter(SampledBallot.vote.isnot(None))
        .join(AuditBoard)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .group_by(AuditBoard.id)
        .values(AuditBoard.id, func.count())
    )

    return {
        ab.id: {
            "numSampledBallots": sampled_ballots_by_audit_board.get(ab.id, 0),
            "numAuditedBallots": audited_ballots_by_audit_board.get(ab.id, 0),
        }
        for ab in audit_boards
    }


def serialize_audit_board(audit_board: AuditBoard, round_status: JSONDict) -> JSONDict:
    return {
        "id": audit_board.id,
        "name": audit_board.name,
        "signedOffAt": isoformat(audit_board.signed_off_at),
        "currentRoundStatus": round_status,
    }


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board",
    methods=["GET"],
)
@with_jurisdiction_access
def list_audit_boards(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    round = Round.query.get_or_404(round_id)
    audit_boards = (
        AuditBoard.query.filter_by(jurisdiction_id=jurisdiction.id, round_id=round_id)
        .order_by(AuditBoard.name)
        .all()
    )
    round_status = round_status_by_audit_board(jurisdiction.id, round_id)
    json_audit_boards = [
        serialize_audit_board(ab, round_status[ab.id]) for ab in audit_boards
    ]
    return jsonify({"auditBoards": json_audit_boards})


def calculate_risk_measurements(election: Election, round: Round):
    results = sample_results(election)

    for contest in election.contests:
        risk, is_complete = bravo.compute_risk(
            election.risk_limit / 100,
            sampler_contest.from_db_contest(contest),
            results[contest.id],
        )

        round_contest = next(
            rc for rc in round.round_contests if rc.contest_id == contest.id
        )
        round_contest.end_p_value = max(risk.values())
        round_contest.is_complete = is_complete


def end_round(election: Election, round: Round):
    calculate_risk_measurements(election, round)
    round.ended_at = datetime.utcnow()


def is_round_complete(election: Election, round: Round) -> bool:
    num_jurisdictions_without_audit_boards_set_up = (
        # For each jurisdiction...
        Jurisdiction.query.filter_by(election_id=election.id)
        # Where there are ballots that haven't been audited...
        .join(Jurisdiction.batches)
        .join(Batch.ballots)
        .filter(SampledBallot.vote.is_(None))
        # And those ballots got sampled this round...
        .join(SampledBallot.draws)
        .filter_by(round_id=round.id)
        # Count the number of audit boards set up.
        .outerjoin(
            AuditBoard,
            and_(
                AuditBoard.jurisdiction_id == Jurisdiction.id,
                AuditBoard.round_id == round.id,
            ),
        )
        .group_by(Jurisdiction.id)
        # Finally, count how many jurisdictions have no audit boards set up.
        .having(func.count(AuditBoard.id) == 0)
        .count()
    )
    all_audit_boards_set_up = num_jurisdictions_without_audit_boards_set_up == 0
    all_audit_boards_signed_off = all(
        ab.signed_off_at is not None for ab in round.audit_boards
    )
    return all_audit_boards_set_up and all_audit_boards_signed_off


SIGN_OFF_AUDIT_BOARD_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "memberName1": {"type": "string"},
        "memberName2": {"type": "string"},
    },
    "additionalProperties": False,
    "required": ["memberName1", "memberName2"],
}

# Raises if invalid
def validate_sign_off(sign_off_request: JSONDict, audit_board: AuditBoard):
    validate(sign_off_request, SIGN_OFF_AUDIT_BOARD_REQUEST_SCHEMA)

    for name in [sign_off_request["memberName1"], sign_off_request["memberName2"]]:
        if name not in {audit_board.member_1, audit_board.member_2}:
            raise BadRequest(f"Audit board member name did not match: {name}")

    if any(b.vote is None for b in audit_board.sampled_ballots):
        raise Conflict(f"Audit board is not finished auditing all assigned ballots")


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/sign-off",
    methods=["POST"],
)
@with_audit_board_access
def sign_off_audit_board(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,
    audit_board: AuditBoard,
):
    validate_sign_off(request.get_json(), audit_board)

    audit_board.signed_off_at = datetime.utcnow()

    if is_round_complete(election, round):
        end_round(election, round)

    db.session.commit()

    return jsonify(status="ok")
