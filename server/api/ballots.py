import io, csv
from typing import Optional, TextIO
from sqlalchemy import func, literal_column, and_
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.dialects.postgresql import aggregate_order_by
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict


from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from .shared import get_current_round
from ..models import *  # pylint: disable=wildcard-import
from ..util.csv_download import csv_response, jurisdiction_timestamp_name
from ..util.jsonschema import JSONDict, validate
from ..util.get_json import safe_get_json_dict


def ballot_retrieval_list(jurisdiction: Jurisdiction, round: Round) -> TextIO:
    previous_ballots = set(
        SampledBallotDraw.query.join(Round)
        .filter(Round.round_num < round.round_num)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .values(Batch.tabulator, Batch.name, SampledBallot.ballot_position)
    )

    ballots = list(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .outerjoin(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .join(SampledBallot.audit_board)
        .group_by(AuditBoard.id, SampledBallot.id, Batch.id, CvrBallot.imprinted_id)
        .order_by(
            func.human_sort(AuditBoard.name),
            func.human_sort(Batch.container),
            func.human_sort(Batch.tabulator),
            func.human_sort(Batch.name),
            SampledBallot.ballot_position,
        )
        .values(
            Batch.container,
            Batch.tabulator,
            Batch.name,
            SampledBallot.ballot_position,
            CvrBallot.imprinted_id,
            func.string_agg(
                SampledBallotDraw.ticket_number,
                aggregate_order_by(
                    literal_column("','"), SampledBallotDraw.ticket_number
                ),
            ),
            AuditBoard.name,
        )
    )

    show_imprinted_id = jurisdiction.election.audit_type in [
        AuditType.BALLOT_COMPARISON,
        AuditType.HYBRID,
    ]
    show_container = len(ballots) > 0 and ballots[0][0] is not None
    show_tabulator = len(ballots) > 0 and ballots[0][1] is not None

    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    columns_to_show = [
        ("Container", show_container),
        ("Tabulator", show_tabulator),
        ("Batch Name", True),
        ("Ballot Number", True),
        ("Imprinted ID", show_imprinted_id),
        ("Ticket Numbers", True),
        ("Already Audited", True),
        ("Audit Board", True),
    ]
    retrieval_list_writer.writerow(
        [header for header, should_show in columns_to_show if should_show]
    )

    for ballot in ballots:
        (
            container,
            tabulator,
            batch_name,
            position,
            imprinted_id,
            ticket_numbers,
            audit_board_name,
        ) = ballot
        previously_audited = (
            "Y" if (tabulator, batch_name, position) in previous_ballots else "N"
        )
        values_to_show = [
            (container, show_container),
            (tabulator, show_tabulator),
            (batch_name, True),
            (position, True),
            (imprinted_id, show_imprinted_id),
            (ticket_numbers, True),
            (previously_audited, True),
            (audit_board_name, True),
        ]
        retrieval_list_writer.writerow(
            [value for value, should_show in values_to_show if should_show]
        )

    csv_io.seek(0)
    return csv_io


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballots/retrieval-list",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def get_retrieval_list(election: Election, jurisdiction: Jurisdiction, round: Round):
    retrieval_list_csv = ballot_retrieval_list(jurisdiction, round)
    return csv_response(
        retrieval_list_csv,
        filename=f"ballot-retrieval-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
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
        has_invalid_write_in=interpretation["hasInvalidWriteIn"],
    )


def serialize_interpretation(interpretation: BallotInterpretation) -> JSONDict:
    return {
        "contestId": interpretation.contest_id,
        "interpretation": interpretation.interpretation,
        "choiceIds": [choice.id for choice in interpretation.selected_choices],
        "comment": interpretation.comment,
        "hasInvalidWriteIn": interpretation.has_invalid_write_in,
    }


def serialize_ballot(
    ballot: SampledBallot, audit_type: AuditType, imprinted_id: Optional[str]
) -> JSONDict:
    batch = ballot.batch
    audit_board = ballot.audit_board
    json_ballot = {
        "id": ballot.id,
        "status": ballot.status,
        "interpretations": [
            serialize_interpretation(i) for i in ballot.interpretations
        ],
        "position": ballot.ballot_position,
        "batch": {
            "id": batch.id,
            "name": batch.name,
            "tabulator": batch.tabulator,
            "container": batch.container,
        },
        "auditBoard": audit_board and {"id": audit_board.id, "name": audit_board.name},
    }
    if audit_type in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        json_ballot["imprintedId"] = imprinted_id
    return json_ballot


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballots",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def list_ballots_for_jurisdiction(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    if request.args.get("count"):
        count = (
            SampledBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction.id)
            .join(SampledBallotDraw)
            .filter_by(round_id=round.id)
            .distinct(SampledBallot.id)
            .count()
        )
        return jsonify({"count": count})

    ballots = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallotDraw)
        .filter_by(round_id=round.id)
        .outerjoin(SampledBallot.audit_board)
        .outerjoin(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .order_by(
            func.human_sort(AuditBoard.name),
            func.human_sort(Batch.container),
            func.human_sort(Batch.tabulator),
            func.human_sort(Batch.name),
            SampledBallot.ballot_position,
        )
        .with_entities(SampledBallot, CvrBallot.imprinted_id)
        .options(
            contains_eager(SampledBallot.batch),
            contains_eager(SampledBallot.audit_board),
            joinedload(SampledBallot.interpretations)
            .joinedload(BallotInterpretation.selected_choices)
            .load_only(ContestChoice.id),
        )
        .all()
    )
    json_ballots = [
        serialize_ballot(ballot, AuditType(election.audit_type), imprinted_id)
        for ballot, imprinted_id in ballots
    ]
    return jsonify({"ballots": json_ballots})


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/ballots",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_BOARD])
def list_ballots_for_audit_board(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,
):
    previously_audited_ballots = (
        SampledBallotDraw.query.join(Round)
        .filter(Round.round_num < round.round_num)
        .join(SampledBallot)
        .with_entities(SampledBallot.id)
        .subquery()
    )
    ballots = (
        SampledBallot.query.filter_by(audit_board_id=audit_board.id)
        .filter(SampledBallot.id.notin_(previously_audited_ballots))
        .join(Batch)
        .outerjoin(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .order_by(
            func.human_sort(Batch.container),
            func.human_sort(Batch.tabulator),
            func.human_sort(Batch.name),
            SampledBallot.ballot_position,
        )
        .with_entities(SampledBallot, CvrBallot.imprinted_id)
        .options(
            contains_eager(SampledBallot.batch),
            joinedload(SampledBallot.interpretations)
            .joinedload(BallotInterpretation.selected_choices)
            .load_only(ContestChoice.id),
        )
        .all()
    )
    json_ballots = [
        serialize_ballot(ballot, AuditType(election.audit_type), imprinted_id)
        for ballot, imprinted_id in ballots
    ]
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
        "hasInvalidWriteIn": {"type": "boolean"},
    },
    "additionalProperties": False,
    "required": [
        "contestId",
        "interpretation",
        "choiceIds",
        "comment",
        "hasInvalidWriteIn",
    ],
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

    if (
        interpretation["interpretation"] == Interpretation.CONTEST_NOT_ON_BALLOT
        and interpretation["hasInvalidWriteIn"]
    ):
        raise BadRequest(
            f"Cannot specify hasInvalidWriteIn=True with interpretation {Interpretation.CONTEST_NOT_ON_BALLOT} for contest {interpretation['contestId']}"
        )


def validate_audit_ballot(ballot_audit: JSONDict, jurisdiction: Jurisdiction):
    validate(ballot_audit, AUDIT_BALLOT_SCHEMA)

    if ballot_audit["status"] == BallotStatus.AUDITED:
        if len(ballot_audit["interpretations"]) != len(list(jurisdiction.contests)):
            raise BadRequest("Must include an interpretation for each contest.")
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
@restrict_access([UserType.AUDIT_BOARD])
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
    current_round = get_current_round(election)
    assert current_round is not None  # Otherwise ballot would be not found above
    if any(draw.round_id != current_round.id for draw in ballot.draws):
        raise Conflict("Ballot was already audited in a previous round")

    ballot_audit = safe_get_json_dict(request)
    validate_audit_ballot(ballot_audit, jurisdiction)

    ballot.status = ballot_audit["status"]
    ballot.interpretations = [
        deserialize_interpretation(ballot.id, interpretation)
        for interpretation in ballot_audit["interpretations"]
    ]

    db_session.commit()

    return jsonify(status="ok")
