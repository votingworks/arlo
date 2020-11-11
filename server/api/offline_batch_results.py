from typing import List
from datetime import datetime
from collections import defaultdict
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import is_round_complete, end_round, get_current_round, sampled_all_ballots
from ..util.jsonschema import JSONDict, validate
from ..util.isoformat import isoformat

OFFLINE_BATCH_RESULTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "batchName": {"type": "string"},
            "choiceResults": {
                "type": "object",
                "patternProperties": {"^.*$": {"type": "integer", "minimum": 0},},
            },
        },
        "required": ["batchName", "choiceResults"],
        "additionalProperties": False,
    },
}


def validate_offline_batch_results(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
    offline_batch_results: List[JSONDict],
):
    if len(list(election.contests)) > 1:
        raise Conflict("Offline batch results only supported for single contest audits")

    contest = list(election.contests)[0]

    if not any(c.id == contest.id for c in jurisdiction.contests):
        raise Conflict("Jurisdiction not in contest universe")

    if not sampled_all_ballots(round, election):
        raise Conflict(
            "Offline batch results only supported if all ballots are sampled"
        )

    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(f"Round {round.round_num} is not the current round")

    num_audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).count()
    if num_audit_boards == 0:
        raise Conflict("Must set up audit boards before recording results")

    validate(offline_batch_results, OFFLINE_BATCH_RESULTS_SCHEMA)

    contest_choice_ids = {choice.id for choice in contest.choices}

    for batch_results in offline_batch_results:
        if set(batch_results["choiceResults"].keys()) != contest_choice_ids:
            raise BadRequest(
                f"Invalid choice ids for batch {batch_results['batchName']}"
            )

    # TODO validate total results does not exceed ballot manifest


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/results/batch",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def record_offline_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    offline_batch_results = request.get_json()
    validate_offline_batch_results(election, jurisdiction, round, offline_batch_results)

    OfflineBatchResult.query.filter_by(jurisdiction_id=jurisdiction.id).delete()
    for batch_results in offline_batch_results:
        for contest_choice_id, result in batch_results["choiceResults"].items():
            db_session.add(
                OfflineBatchResult(
                    jurisdiction_id=jurisdiction.id,
                    batch_name=batch_results["batchName"],
                    contest_choice_id=contest_choice_id,
                    result=result,
                )
            )

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/results/batch/finalize",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def finalize_offline_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    jurisdiction.finalized_offline_batch_results_at = datetime.utcnow()

    sum_results_by_choice = (
        OfflineBatchResult.query.filter_by(jurisdiction_id=jurisdiction.id)
        .group_by(OfflineBatchResult.contest_choice_id)
        .values(
            OfflineBatchResult.contest_choice_id, func.sum(OfflineBatchResult.result)
        )
    )

    # We only support one contest for now
    contest = list(election.contests)[0]

    for choice_id, sum_result in sum_results_by_choice:
        db_session.add(
            JurisdictionResult(
                round_id=round.id,
                contest_id=contest.id,
                jurisdiction_id=jurisdiction.id,
                contest_choice_id=choice_id,
                result=sum_result,
            )
        )

    if is_round_complete(election, round):
        end_round(election, round)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/results/batch",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_offline_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,  # pylint: disable=unused-argument
):
    # We only support one contest for now
    contest = list(election.contests)[0]

    recorded_results = list(
        OfflineBatchResult.query.filter_by(jurisdiction_id=jurisdiction.id)
        .order_by(OfflineBatchResult.created_at)
        .all()
    )
    # We want to display batches in the order the user created them. Dict keys
    # are ordered, so we use a dict to dedupe the batch names while preserving
    # order.
    ordered_batch_names = list(
        dict.fromkeys(result.batch_name for result in recorded_results)
    )

    results_by_batch: JSONDict = defaultdict(
        lambda: {choice.id: None for choice in contest.choices}
    )
    for result in recorded_results:
        results_by_batch[result.batch_name][result.contest_choice_id] = result.result

    results = [
        {"batchName": batch_name, "choiceResults": results_by_batch[batch_name],}
        for batch_name in ordered_batch_names
    ]

    return jsonify(
        {
            "finalizedAt": isoformat(jurisdiction.finalized_offline_batch_results_at),
            "results": results,
        }
    )
