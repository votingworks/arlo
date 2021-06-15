import uuid
import itertools
from datetime import datetime
from typing import List, Dict
from flask import jsonify, request, current_app
from xkcdpass import xkcd_password as xp
from werkzeug.exceptions import Conflict, BadRequest, InternalServerError
from sqlalchemy import func

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from .rounds import get_current_round, is_round_complete, end_round
from ..util.jsonschema import validate, JSONDict
from ..util.binpacking import BalancedBucketList, Bucket
from ..util.isoformat import isoformat
from ..activity_log.activity_log import (
    AuditBoardSignOff,
    CreateAuditBoards,
    record_activity,
    activity_base,
)

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

    if len(set(ab["name"] for ab in audit_boards)) != len(audit_boards):
        raise BadRequest("Audit board names must be unique")


def assign_sampled_ballots(
    jurisdiction: Jurisdiction, round: Round, audit_boards: List[AuditBoard],
):
    # If containers were provided, we want all ballots from the same container
    # assigned to the same audit board. So we key batches by container.
    # Otherwise, key batches normally by tabulator+name.
    use_container = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallot.draws)
        .filter_by(round_id=round.id)
        .value(Batch.container)
        is not None
    )

    # Count sampled ballots for each batch, grouping batches by key.
    ballot_counts_by_batch = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallot.draws)
        .filter_by(round_id=round.id)
    )
    if use_container:
        ballot_counts_by_batch = ballot_counts_by_batch.group_by(
            Batch.container
        ).values(Batch.container, func.count(SampledBallot.id.distinct()))
    else:
        ballot_counts_by_batch = (
            ((tabulator, batch_name), num_ballots)
            for tabulator, batch_name, num_ballots in ballot_counts_by_batch.group_by(
                Batch.tabulator, Batch.name
            ).values(
                Batch.tabulator, Batch.name, func.count(SampledBallot.id.distinct())
            )
        )

    # Divvy up batches of ballots between the audit boards.
    # Note: BalancedBucketList doesn't care which buckets have which batches to
    # start, so we add all the batches to the first bucket before balancing.
    buckets = [Bucket(audit_board.id) for audit_board in audit_boards]
    for batch_key, num_ballots in ballot_counts_by_batch:
        buckets[0].add_batch(batch_key, num_ballots)
    balanced_buckets = BalancedBucketList(buckets)

    # Set the audit board in the database for each bucket of ballots.
    for bucket in balanced_buckets.buckets:
        for batch_key in bucket.batches:

            if use_container:
                batch_filter = dict(container=batch_key)
            else:
                tabulator, batch_name = batch_key
                batch_filter = dict(tabulator=tabulator, name=batch_name)

            db_session.execute(
                SampledBallot.__table__.update()  # pylint: disable=no-member
                .values(audit_board_id=bucket.name)
                .where(
                    SampledBallot.batch_id.in_(
                        Batch.query.filter_by(
                            jurisdiction_id=jurisdiction.id, **batch_filter,
                        )
                        .with_entities(Batch.id)
                        .subquery()
                    )
                )
                .where(
                    SampledBallot.id.in_(
                        SampledBallotDraw.query.filter_by(round_id=round.id)
                        .with_entities(SampledBallotDraw.ballot_id)
                        .subquery()
                    )
                )
            )

    # We saw a bug where not all ballots got assigned to an audit board. Since
    # we couldn't reproduce it, we check to make sure that didn't happen. If it
    # did, we rollback the transaction and fail the request.
    ballots_query = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallot.draws)
        .filter_by(round_id=round.id)
    )
    num_sampled_ballots = ballots_query.count()
    num_assigned_ballots = ballots_query.filter(
        SampledBallot.audit_board_id.isnot(None)
    ).count()
    if num_sampled_ballots != num_assigned_ballots:  # pragma: no cover
        current_app.logger.error(
            "ERROR_BALLOTS_NOT_ASSIGNED "
            + str(
                dict(
                    jurisdiction_id=jurisdiction.id,
                    round_id=round.id,
                    num_sampled_ballots=num_sampled_ballots,
                    num_assigned_ballots=num_assigned_ballots,
                    buckets=balanced_buckets,
                )
            )
        )
        raise InternalServerError("Error assigning ballots to audit boards")


def assign_sampled_batches(
    jurisdiction: Jurisdiction, round: Round, audit_boards: List[AuditBoard]
):
    sampled_batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .order_by(Batch.created_at)
        .all()
    )
    audit_board_generator = itertools.cycle(audit_boards)
    for batch in sampled_batches:
        batch.audit_board_id = next(audit_board_generator).id
        db_session.add(batch)


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def create_audit_boards(election: Election, jurisdiction: Jurisdiction, round: Round):
    json_audit_boards = request.get_json()
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
    db_session.add_all(audit_boards)

    if election.audit_type == AuditType.BATCH_COMPARISON:
        assign_sampled_batches(jurisdiction, round, audit_boards)
    else:
        assign_sampled_ballots(jurisdiction, round, audit_boards)

    record_activity(
        CreateAuditBoards(
            timestamp=datetime.now(timezone.utc),
            base=activity_base(election),
            jurisdiction_id=jurisdiction.id,
            jurisdiction_name=jurisdiction.name,
            num_audit_boards=len(audit_boards),
        )
    )

    db_session.commit()

    return jsonify(status="ok")


def round_status_by_audit_board(
    jurisdiction_id: str, round_id: str
) -> Dict[str, JSONDict]:
    audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_id, round_id=round_id
    ).all()
    sampled_ballots_by_audit_board = dict(
        SampledBallot.query.join(AuditBoard)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .group_by(AuditBoard.id)
        .values(AuditBoard.id, func.count())
    )
    audited_ballots_by_audit_board = dict(
        SampledBallot.query.join(AuditBoard)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
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
        "passphrase": audit_board.passphrase,
        "signedOffAt": isoformat(audit_board.signed_off_at),
        "currentRoundStatus": round_status,
    }


def serialize_members(audit_board):
    members = []

    for i in range(0, 2):
        name = getattr(audit_board, f"member_{i + 1}")
        affiliation = getattr(audit_board, f"member_{i + 1}_affiliation")

        if not name:
            break

        members.append({"name": name, "affiliation": affiliation})

    return members


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def list_audit_boards(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    audit_boards = (
        AuditBoard.query.filter_by(jurisdiction_id=jurisdiction.id, round_id=round.id)
        .order_by(func.human_sort(AuditBoard.name))
        .all()
    )
    round_status = round_status_by_audit_board(jurisdiction.id, round.id)
    json_audit_boards = [
        serialize_audit_board(ab, round_status[ab.id]) for ab in audit_boards
    ]
    return jsonify({"auditBoards": json_audit_boards})


MEMBER_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "affiliation": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [affiliation.value for affiliation in Affiliation],
                },
                {"type": "null"},
            ]
        },
    },
    "additionalProperties": False,
    "required": ["name", "affiliation"],
}

SET_MEMBERS_SCHEMA = {
    "type": "array",
    "items": MEMBER_SCHEMA,
}


def validate_members(members: List[JSONDict]):
    # You can do all of these checks using JSON schema, but the resulting error
    # messages aren't very good.
    if len(members) == 0:
        raise BadRequest("Must have at least one member.")
    if len(members) > 2:
        raise BadRequest("Cannot have more than two members.")

    validate(members, SET_MEMBERS_SCHEMA)

    for member in members:
        if member["name"] == "":
            raise BadRequest("'name' must not be empty.")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/members",
    methods=["PUT"],
)
@restrict_access([UserType.AUDIT_BOARD])
def set_audit_board_members(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,
):
    members = request.get_json()
    validate_members(members)

    audit_board.member_1 = members[0]["name"].strip()
    audit_board.member_1_affiliation = members[0]["affiliation"]
    if len(members) > 1:
        audit_board.member_2 = members[1]["name"].strip()
        audit_board.member_2_affiliation = members[1]["affiliation"]

    db_session.commit()

    return jsonify(status="ok")


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

    if sign_off_request["memberName1"].strip() != audit_board.member_1:
        raise BadRequest(
            f"Audit board member name did not match: {sign_off_request['memberName1']}"
        )

    if (
        audit_board.member_2
        and sign_off_request["memberName2"].strip() != audit_board.member_2
    ):
        raise BadRequest(
            f"Audit board member name did not match: {sign_off_request['memberName2']}"
        )

    if any(b.status == BallotStatus.NOT_AUDITED for b in audit_board.sampled_ballots):
        raise Conflict("Audit board is not finished auditing all assigned ballots")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/sign-off",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_BOARD])
def sign_off_audit_board(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,
    audit_board: AuditBoard,
):
    validate_sign_off(request.get_json(), audit_board)

    audit_board.signed_off_at = datetime.now(timezone.utc)

    assert audit_board.name
    record_activity(
        AuditBoardSignOff(
            timestamp=audit_board.signed_off_at,
            base=activity_base(election),
            jurisdiction_id=jurisdiction.id,
            jurisdiction_name=jurisdiction.name,
            audit_board_name=audit_board.name,
        )
    )

    if is_round_complete(election, round):
        end_round(election, round)

    db_session.commit()

    return jsonify(status="ok")
