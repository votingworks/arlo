import enum
from typing import List
from datetime import datetime, timezone
from collections import defaultdict
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy import func

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import get_current_round, is_full_hand_tally
from ..util.jsonschema import JSONDict, validate
from ..util.isoformat import isoformat
from ..util.get_json import safe_get_json_dict


class BatchType(str, enum.Enum):
    ABSENTEE_BY_MAIL = "Absentee By Mail"
    ADVANCE = "Advance"
    ELECTION_DAY = "Election Day"
    PROVISIONAL = "Provisional"
    OTHER = "Other"


FULL_HAND_TALLY_BATCH_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "batchName": {"type": "string", "minLength": 1, "maxLength": 200},
        "batchType": {
            "type": "string",
            "enum": [batch_type.value for batch_type in BatchType],
        },
        "choiceResults": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 1000 * 1000 * 1000,
                },
            },
        },
    },
    "required": ["batchName", "batchType", "choiceResults"],
    "additionalProperties": False,
}


def validate_full_hand_tally_batch_result_request(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
):
    if len(list(election.contests)) > 1:
        raise Conflict(
            "Full hand tally only supported for single contest audits"
        )  # pragma: no cover

    # We only support one contest for now
    contest = list(election.contests)[0]

    if not any(c.id == contest.id for c in jurisdiction.contests):
        raise Conflict("Jurisdiction not in contest universe")  # pragma: no cover

    if not is_full_hand_tally(round, election):
        raise Conflict(
            "Full hand tally only supported if all ballots are sampled"
        )  # pragma: no cover

    if jurisdiction.finalized_full_hand_tally_results_at is not None:
        raise Conflict("Results have already been finalized")

    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(
            f"Round {round.round_num} is not the current round"
        )  # pragma: no cover

    num_audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).count()
    if num_audit_boards == 0:
        raise Conflict(
            "Must set up audit boards before recording results"
        )  # pragma: no cover


def validate_full_hand_tally_batch_result(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
    batch_result: JSONDict,
):
    validate_full_hand_tally_batch_result_request(election, jurisdiction, round)

    validate(batch_result, FULL_HAND_TALLY_BATCH_RESULT_SCHEMA)

    # We only support one contest for now
    contest = list(election.contests)[0]
    contest_choice_ids = {choice.id for choice in contest.choices}

    if set(batch_result["choiceResults"].keys()) != contest_choice_ids:
        raise BadRequest(f"Invalid choice ids for batch {batch_result['batchName']}")


def serialize_full_hand_tally_batch_results(
    results: List[FullHandTallyBatchResult], contest: Contest
) -> List[JSONDict]:
    # We want to display batches in the order the user created them. Dict keys
    # are ordered, so we use a dict to dedupe the batch names while preserving
    # order. (Assumes results is already ordered by created_at)
    ordered_batches = list(
        dict.fromkeys((result.batch_name, result.batch_type) for result in results)
    )

    results_by_batch: JSONDict = defaultdict(
        lambda: {choice.id: None for choice in contest.choices}
    )
    for result in results:
        results_by_batch[result.batch_name][result.contest_choice_id] = result.result

    json_results = [
        {
            "batchName": batch_name,
            "batchType": batch_type,
            "choiceResults": results_by_batch[batch_name],
        }
        for batch_name, batch_type in ordered_batches
    ]
    return json_results


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/batch/",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def add_full_hand_tally_batch_result(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    batch_result = safe_get_json_dict(request)
    validate_full_hand_tally_batch_result(election, jurisdiction, round, batch_result)

    if FullHandTallyBatchResult.query.filter_by(
        jurisdiction_id=jurisdiction.id, batch_name=batch_result["batchName"]
    ).first():
        raise Conflict("Batch names must be unique")

    for contest_choice_id, result in batch_result["choiceResults"].items():
        db_session.add(
            FullHandTallyBatchResult(
                jurisdiction_id=jurisdiction.id,
                batch_name=batch_result["batchName"],
                batch_type=batch_result["batchType"],
                contest_choice_id=contest_choice_id,
                result=result,
            )
        )

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/batch/<path:batch_name>",
    methods=["PUT"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def update_full_hand_tally_batch_result(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
    batch_name: str,
):
    batch_result = safe_get_json_dict(request)
    validate_full_hand_tally_batch_result(election, jurisdiction, round, batch_result)

    if (
        batch_name != batch_result["batchName"]
        and FullHandTallyBatchResult.query.filter_by(
            jurisdiction_id=jurisdiction.id, batch_name=batch_result["batchName"]
        ).first()
    ):
        raise Conflict("Batch names must be unique")

    for contest_choice_id, result in batch_result["choiceResults"].items():
        new_batch_result = FullHandTallyBatchResult.query.filter_by(
            jurisdiction_id=jurisdiction.id,
            batch_name=batch_name,
            contest_choice_id=contest_choice_id,
        ).one_or_none()
        if new_batch_result is None:
            raise Conflict("This batch has been deleted")

        new_batch_result.batch_name = batch_result["batchName"]
        new_batch_result.batch_type = batch_result["batchType"]
        new_batch_result.result = result
        db_session.add(new_batch_result)

    db_session.commit()

    return jsonify(status="ok")


# We use the `path:` converter for the batch_name parameter because it's
# URI-encoded and we want to decode it with support for slashes
@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/batch/<path:batch_name>",
    methods=["DELETE"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def delete_full_hand_tally_batch_result(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,  # pylint: disable=unused-argument
    batch_name: str,
):
    validate_full_hand_tally_batch_result_request(election, jurisdiction, round)

    FullHandTallyBatchResult.query.filter_by(
        jurisdiction_id=jurisdiction.id, batch_name=batch_name
    ).delete()

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/finalize",
    methods=["POST"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def finalize_full_hand_tally_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    jurisdiction.finalized_full_hand_tally_results_at = datetime.now(timezone.utc)

    sum_results_by_choice = (
        FullHandTallyBatchResult.query.filter_by(jurisdiction_id=jurisdiction.id)
        .group_by(FullHandTallyBatchResult.contest_choice_id)
        .values(
            FullHandTallyBatchResult.contest_choice_id,
            func.sum(FullHandTallyBatchResult.result),
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

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/finalize",
    methods=["DELETE"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def unfinalize_full_hand_tally_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,
):
    if jurisdiction.finalized_full_hand_tally_results_at is None:
        raise Conflict("Results have not been finalized")

    if round.ended_at is not None:
        raise Conflict("Results cannot be unfinalized after the audit round ends")

    jurisdiction.finalized_full_hand_tally_results_at = None

    JurisdictionResult.query.filter_by(
        round_id=round.id,
        jurisdiction_id=jurisdiction.id,
    ).delete()

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/full-hand-tally/batch",
    methods=["GET"],
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def get_full_hand_tally_batch_results(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,  # pylint: disable=unused-argument
):
    # We only support one contest for now
    contest = list(election.contests)[0]

    results = list(
        FullHandTallyBatchResult.query.filter_by(jurisdiction_id=jurisdiction.id)
        .order_by(FullHandTallyBatchResult.created_at)
        .all()
    )

    return jsonify(
        {
            "finalizedAt": isoformat(jurisdiction.finalized_full_hand_tally_results_at),
            "results": serialize_full_hand_tally_batch_results(results, contest),
        }
    )
