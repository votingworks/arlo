import io, csv
from typing import List
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..auth import with_jurisdiction_access
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import is_round_complete, end_round, get_current_round
from ..util.csv_download import csv_response, election_timestamp_name
from ..util.jsonschema import JSONDict, validate
from ..util.group_by import group_by


def already_audited_batch_ids(jurisdiction: Jurisdiction, round: Round) -> List[str]:
    return [
        batch_id
        for batch_id, in Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .join(Round)
        .filter(Round.round_num < round.round_num)
        .values(Batch.id)
    ]


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/retrieval-list",
    methods=["GET"],
)
@with_jurisdiction_access
def get_batch_retrieval_list(
    election: Election, jurisdiction: Jurisdiction, round_id: str
):
    round = get_or_404(Round, round_id)

    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round_id)
        .filter(Batch.id.notin_(already_audited_batch_ids(jurisdiction, round)))
        .join(AuditBoard)
        .group_by(AuditBoard.id, Batch.id)
        .order_by(AuditBoard.name, Batch.name)
        .values(Batch.name, Batch.storage_location, Batch.tabulator, AuditBoard.name,)
    )
    retrieval_list_rows = [
        ["Batch Name", "Storage Location", "Tabulator", "Audit Board",]
    ] + [list(batch_tuple) for batch_tuple in batches]

    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerows(retrieval_list_rows)

    return csv_response(
        csv_io.getvalue(),
        filename=f"batch-retrieval-{election_timestamp_name(election)}.csv",
    )


def serialize_batch(batch: Batch) -> JSONDict:
    audit_board = batch.audit_board
    return {
        "id": batch.id,
        "name": batch.name,
        "numBallots": batch.num_ballots,
        "auditBoard": audit_board and {"id": audit_board.id, "name": audit_board.name},
    }


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches",
    methods=["GET"],
)
@with_jurisdiction_access
def list_batches_for_jurisdiction(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    round = get_or_404(Round, round_id)

    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round_id)
        .filter(Batch.id.notin_(already_audited_batch_ids(jurisdiction, round)))
        .outerjoin(AuditBoard)
        .order_by(AuditBoard.name, Batch.name)
        .all()
    )

    return jsonify({"batches": [serialize_batch(batch) for batch in batches]})


BATCH_RESULTS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^.*$": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "integer", "minimum": 0}},
        }
    },
}


def validate_batch_results(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
    batch_results: JSONDict,
):
    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(f"Round {round.round_num} is not the current round")

    num_audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).count()
    if num_audit_boards == 0:
        raise Conflict("Must set up audit boards before recording results")

    validate(batch_results, BATCH_RESULTS_SCHEMA)

    batches = list(
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .order_by(Batch.name)
        .all()
    )

    if set(batch_results.keys()) != {batch.id for batch in batches}:
        raise BadRequest("Invalid batch ids")

    # For now, we only support one contest for batch audits
    contest = list(jurisdiction.contests)[0]
    contest_choice_ids = {choice.id for choice in contest.choices}

    for batch in batches:
        if set(batch_results[batch.id].keys()) != contest_choice_ids:
            raise BadRequest(f"Invalid choice ids for batch {batch.name}")

        total_votes = sum(batch_results[batch.id].values())
        allowed_votes = batch.num_ballots * contest.votes_allowed
        if total_votes > allowed_votes:
            raise BadRequest(
                f"Total votes for batch {batch.name} should not exceed {allowed_votes}"
                f" - the number of ballots in the batch ({batch.num_ballots})"
                f" times the number of votes allowed ({contest.votes_allowed})."
            )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/results",
    methods=["PUT"],
)
@with_jurisdiction_access
def record_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    round = get_or_404(Round, round_id)

    batch_results = request.get_json()
    validate_batch_results(election, jurisdiction, round, batch_results)

    for batch_id, results_by_choice in batch_results.items():
        for contest_choice_id, result in results_by_choice.items():
            db_session.add(
                BatchResult(
                    batch_id=batch_id,
                    contest_choice_id=contest_choice_id,
                    result=result,
                )
            )

    if is_round_complete(election, round):
        end_round(election, round)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/results",
    methods=["GET"],
)
@with_jurisdiction_access
def get_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    round = get_or_404(Round, round_id)

    results = list(
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round_id)
        .filter(Batch.id.notin_(already_audited_batch_ids(jurisdiction, round)))
        .join(Jurisdiction)
        .join(Jurisdiction.contests)
        .join(ContestChoice)
        .outerjoin(
            BatchResult,
            and_(
                BatchResult.batch_id == Batch.id,
                BatchResult.contest_choice_id == ContestChoice.id,
            ),
        )
        .values(Batch.id, ContestChoice.id, BatchResult.result)
    )
    results_by_batch = group_by(results, lambda result: result[0])  # batch_id

    batch_results = {
        batch_id: {choice_id: result for (_, choice_id, result) in batch_results}
        for batch_id, batch_results in results_by_batch.items()
    }

    return jsonify(batch_results)
