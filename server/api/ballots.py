import io, csv
from sqlalchemy import func, literal_column
from sqlalchemy.orm import contains_eager
from sqlalchemy.dialects.postgresql import aggregate_order_by
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from . import api
from ..auth import with_jurisdiction_access, with_audit_board_access
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.csv_download import csv_response, election_timestamp_name
from ..util.jsonschema import JSONDict, validate


def ballot_retrieval_list(jurisdiction: Jurisdiction, round: Round) -> str:
    previous_ballots = set(
        SampledBallotDraw.query.join(Round)
        .filter(Round.round_num < round.round_num)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .values(Batch.name, SampledBallot.ballot_position)
    )

    ballots = (
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(AuditBoard)
        .group_by(AuditBoard.id, SampledBallot.id, Batch.id)
        .order_by(AuditBoard.name, Batch.name, SampledBallot.ballot_position)
        .values(
            Batch.name,
            SampledBallot.ballot_position,
            Batch.storage_location,
            Batch.tabulator,
            func.string_agg(
                SampledBallotDraw.ticket_number,
                aggregate_order_by(
                    literal_column("','"), SampledBallotDraw.ticket_number
                ),
            ),
            AuditBoard.name,
        )
    )

    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerow(
        [
            "Batch Name",
            "Ballot Number",
            "Storage Location",
            "Tabulator",
            "Ticket Numbers",
            "Already Audited",
            "Audit Board",
        ]
    )

    for ballot in ballots:
        (
            batch_name,
            position,
            storage_location,
            tabulator,
            ticket_numbers,
            audit_board_name,
        ) = ballot
        previously_audited = "Y" if (batch_name, position) in previous_ballots else "N"
        retrieval_list_writer.writerow(
            [
                batch_name,
                position,
                storage_location,
                tabulator,
                ticket_numbers,
                previously_audited,
                audit_board_name,
            ]
        )

    return csv_io.getvalue()


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/retrieval-list",
    methods=["GET"],
)
@with_jurisdiction_access
def get_retrieval_list(election: Election, jurisdiction: Jurisdiction, round_id: str):
    round = get_or_404(Round, round_id)
    retrieval_list_csv = ballot_retrieval_list(jurisdiction, round)
    return csv_response(
        retrieval_list_csv,
        filename=f"ballot-retrieval-{election_timestamp_name(election)}.csv",
    )


def deserialize_interpretation(
    ballot_id: str, interpretation: JSONDict
) -> BallotInterpretation:
    choices = ContestChoice.query.filter(
        ContestChoice.id.in_(interpretation["choiceIds"])
    ).all()
    contest = Contest.query.get(interpretation["contestId"])
    return BallotInterpretation(
        ballot_id=ballot_id,
        contest_id=interpretation["contestId"],
        interpretation=interpretation["interpretation"],
        selected_choices=choices,
        comment=interpretation["comment"],
        is_overvote=len(choices) > contest.votes_allowed,
    )


def serialize_interpretation(interpretation: BallotInterpretation) -> JSONDict:
    return {
        "contestId": interpretation.contest_id,
        "interpretation": interpretation.interpretation,
        "choiceIds": [choice.id for choice in interpretation.selected_choices],
        "comment": interpretation.comment,
    }


def serialize_ballot(ballot: SampledBallot) -> JSONDict:
    batch = ballot.batch
    audit_board = ballot.audit_board
    return {
        "id": ballot.id,
        "status": ballot.status,
        "interpretations": [
            serialize_interpretation(i) for i in ballot.interpretations
        ],
        "position": ballot.ballot_position,
        "batch": {"id": batch.id, "name": batch.name, "tabulator": batch.tabulator,},
        "auditBoard": audit_board and {"id": audit_board.id, "name": audit_board.name,},
    }


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballots",
    methods=["GET"],
)
@with_jurisdiction_access
def list_ballots_for_jurisdiction(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    get_or_404(Round, round_id)
    ballots = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallotDraw)
        .filter_by(round_id=round_id)
        .outerjoin(AuditBoard)
        .order_by(AuditBoard.name, Batch.name, SampledBallot.ballot_position,)
        .options(
            contains_eager(SampledBallot.batch),
            contains_eager(SampledBallot.audit_board),
        )
        .all()
    )
    json_ballots = [serialize_ballot(b) for b in ballots]
    return jsonify({"ballots": json_ballots})


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/ballots",
    methods=["GET"],
)
@with_audit_board_access
def list_ballots_for_audit_board(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,
):
    ballots = (
        SampledBallot.query.filter_by(audit_board_id=audit_board.id)
        .join(Batch)
        .order_by(Batch.name, SampledBallot.ballot_position)
        .options(contains_eager(SampledBallot.batch))
        .all()
    )
    json_ballots = [serialize_ballot(b) for b in ballots]
    return jsonify({"ballots": json_ballots})


BALLOT_INTERPRETATION_SCHEMA = {
    "type": "object",
    "properties": {
        "contestId": {"type": "string"},
        "interpretation": {
            "type": "string",
            "enum": [interpretation.value for interpretation in Interpretation],
        },
        "choiceIds": {"type": "array", "items": {"type": "string"}},
        "comment": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "additionalProperties": False,
    "required": ["contestId", "interpretation", "choiceIds", "comment"],
}

AUDIT_BALLOT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": [status.value for status in BallotStatus]},
        "interpretations": {"type": "array", "items": BALLOT_INTERPRETATION_SCHEMA},
    },
    "additionalProperties": False,
    "required": ["status", "interpretations"],
}


def validate_interpretation(interpretation: JSONDict):
    contest = Contest.query.get(interpretation["contestId"])
    if not contest:
        raise BadRequest(f"Contest not found: {interpretation['contestId']}")

    if interpretation["interpretation"] == Interpretation.VOTE:
        if len(interpretation["choiceIds"]) == 0:
            raise BadRequest(
                f"Must include choiceIds with interpretation {Interpretation.VOTE} for contest {interpretation['contestId']}"
            )
        choices = ContestChoice.query.filter(
            ContestChoice.id.in_(interpretation["choiceIds"])
        ).all()
        missing_choices = set(interpretation["choiceIds"]) - set(c.id for c in choices)
        if len(missing_choices) > 0:
            raise BadRequest(f"Contest choices not found: {', '.join(missing_choices)}")
        for choice in choices:
            if choice.contest_id != interpretation["contestId"]:
                raise BadRequest(
                    f"Contest choice {choice.id} is not associated with contest {interpretation['contestId']}"
                )
    else:
        if len(interpretation["choiceIds"]) > 0:
            raise BadRequest(
                f"Cannot include choiceIds with interpretation {interpretation['interpretation']} for contest {interpretation['contestId']}"
            )


def validate_audit_ballot(ballot_audit: JSONDict):
    validate(ballot_audit, AUDIT_BALLOT_SCHEMA)

    if ballot_audit["status"] == BallotStatus.AUDITED:
        if len(ballot_audit["interpretations"]) == 0:
            raise BadRequest(
                f"Must include interpretations with ballot status {BallotStatus.AUDITED}."
            )
        for interpretation in ballot_audit["interpretations"]:
            validate_interpretation(interpretation)

    else:
        if len(ballot_audit["interpretations"]) > 0:
            raise BadRequest(
                f"Cannot include interpretations with ballot status {ballot_audit['status']}."
            )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/ballots/<ballot_id>",
    methods=["PUT"],
)
@with_audit_board_access
def audit_ballot(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,  # pylint: disable=unused-argument
    ballot_id: str,
):
    ballot = SampledBallot.query.filter_by(
        id=ballot_id, audit_board_id=audit_board.id
    ).first()
    if not ballot:
        raise NotFound()

    ballot_audit = request.get_json()
    validate_audit_ballot(ballot_audit)

    ballot.status = ballot_audit["status"]
    ballot.interpretations = [
        deserialize_interpretation(ballot.id, interpretation)
        for interpretation in ballot_audit["interpretations"]
    ]

    db_session.commit()

    return jsonify(status="ok")
