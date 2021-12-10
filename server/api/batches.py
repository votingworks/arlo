from datetime import datetime
import io, csv
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy.orm import Query, contains_eager
from sqlalchemy import func

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import is_round_complete, end_round, get_current_round
from ..util.csv_download import csv_response, jurisdiction_timestamp_name
from ..util.jsonschema import JSONDict, validate
from ..util.isoformat import isoformat
from ..activity_log.activity_log import (
    FinalizeBatchResults,
    activity_base,
    record_activity,
)


def already_audited_batches(jurisdiction: Jurisdiction, round: Round) -> Query:
    query: Query = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .join(Round)
        .filter(Round.round_num < round.round_num)
        .with_entities(Batch.id)
        .subquery()
    )
    return query


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/retrieval-list",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def get_batch_retrieval_list(
    election: Election, jurisdiction: Jurisdiction, round: Round
):
    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .filter(Batch.id.notin_(already_audited_batches(jurisdiction, round)))
        .join(AuditBoard)
        .group_by(AuditBoard.id, Batch.id)
        .order_by(func.human_sort(AuditBoard.name), func.human_sort(Batch.name))
        .values(Batch.name, Batch.container, Batch.tabulator, AuditBoard.name,)
    )
    retrieval_list_rows = [["Batch Name", "Container", "Tabulator", "Audit Board",]] + [
        list(batch_tuple) for batch_tuple in batches
    ]

    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerows(retrieval_list_rows)
    csv_io.seek(0)

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"batch-retrieval-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


def serialize_batch(batch: Batch) -> JSONDict:
    audit_board = batch.audit_board
    return {
        "id": batch.id,
        "name": batch.name,
        "numBallots": batch.num_ballots,
        "auditBoard": audit_board and {"id": audit_board.id, "name": audit_board.name},
        "results": (
            {result.contest_choice_id: result.result for result in batch.results}
            if len(list(batch.results)) > 0
            else None
        ),
    }


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def list_batches_for_jurisdiction(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .filter(Batch.id.notin_(already_audited_batches(jurisdiction, round)))
        .outerjoin(AuditBoard)
        .outerjoin(BatchResult)
        .order_by(func.human_sort(AuditBoard.name), func.human_sort(Batch.name))
        .options(contains_eager(Batch.results))
        .all()
    )
    results_finalized = BatchResultsFinalized.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).one_or_none()
    return jsonify(
        {
            "batches": [serialize_batch(batch) for batch in batches],
            "resultsFinalizedAt": isoformat(
                results_finalized and results_finalized.created_at
            ),
        }
    )


BATCH_RESULTS_SCHEMA = {
    "type": "object",
    "patternProperties": {"^.*$": {"type": "integer", "minimum": 0}},
}


def validate_batch_results(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
    batch: Batch,
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

    if (
        BatchResultsFinalized.query.filter_by(
            jurisdiction_id=jurisdiction.id, round_id=round.id
        ).one_or_none()
        is not None
    ):
        raise Conflict("Results have already been finalized")

    if any(draw.round_id != current_round.id for draw in batch.draws):
        raise Conflict("Batch was already audited in a previous round")

    validate(batch_results, BATCH_RESULTS_SCHEMA)

    # We only support one contest for batch audits
    assert len(list(jurisdiction.contests)) == 1
    contest = list(jurisdiction.contests)[0]
    contest_choice_ids = {choice.id for choice in contest.choices}

    if batch_results.keys() != contest_choice_ids:
        raise BadRequest("Invalid choice ids")

    total_votes = sum(batch_results.values())
    assert contest.votes_allowed is not None
    allowed_votes = batch.num_ballots * contest.votes_allowed
    if total_votes > allowed_votes:
        raise BadRequest(
            f"Total votes for batch {batch.name} should not exceed {allowed_votes}"
            f" - the number of ballots in the batch ({batch.num_ballots})"
            f" times the number of votes allowed ({contest.votes_allowed})."
        )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/<batch_id>/results",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def record_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
    batch_id: str,
):
    batch = Batch.query.filter_by(id=batch_id).with_for_update().one_or_none()
    if batch is None:
        raise NotFound()
    batch_results = request.get_json()
    validate_batch_results(election, jurisdiction, round, batch, batch_results)

    batch.results = [
        BatchResult(contest_choice_id=choice_id, result=result)
        for choice_id, result in batch_results.items()
    ]
    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/finalize",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def finalize_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    if (
        BatchResultsFinalized.query.filter_by(
            jurisdiction_id=jurisdiction.id, round_id=round.id
        ).one_or_none()
        is not None
    ):
        raise Conflict("Results have already been finalized")

    num_batches_without_results = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .outerjoin(BatchResult)
        .group_by(Batch.id)
        .having(func.count(BatchResult.batch_id) == 0)
        .count()
    )
    if num_batches_without_results > 0:
        raise Conflict(
            "Cannot finalize batch results until all batches have audit results recorded."
        )

    db_session.add(
        BatchResultsFinalized(jurisdiction_id=jurisdiction.id, round_id=round.id)
    )

    record_activity(
        FinalizeBatchResults(
            timestamp=datetime.now(timezone.utc),
            base=activity_base(election),
            jurisdiction_id=jurisdiction.id,
            jurisdiction_name=jurisdiction.name,
        )
    )

    if is_round_complete(election, round):
        end_round(election, round)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/finalize",
    methods=["DELETE"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def unfinalize_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    round = Round.query.with_for_update().get(round.id)
    if round.ended_at is not None:
        raise Conflict("Results cannot be unfinalized after the audit round ends")

    num_deleted = BatchResultsFinalized.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).delete()
    if num_deleted == 0:
        raise Conflict("Results have not been finalized")

    db_session.commit()

    return jsonify(status="ok")
