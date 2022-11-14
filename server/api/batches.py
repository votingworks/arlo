from datetime import datetime
import io, csv
from typing import List, Optional
import uuid
from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy.orm import Query, joinedload
from sqlalchemy import func

from . import api
from ..auth import get_loggedin_user, get_support_user, restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import is_round_complete, end_round, get_current_round
from ..util.csv_download import csv_response, jurisdiction_timestamp_name
from ..util.jsonschema import JSONDict, validate
from ..util.isoformat import isoformat
from ..util.collections import find_first_duplicate
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
        .group_by(Batch.id)
        .order_by(func.human_sort(Batch.name))
        .values(Batch.name, Batch.container, Batch.tabulator)
    )
    retrieval_list_rows = [["Batch Name", "Container", "Tabulator"]] + [
        list(batch_tuple) for batch_tuple in batches
    ]

    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerows(retrieval_list_rows)

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"batch-retrieval-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


def serialize_batch(batch: Batch) -> JSONDict:
    return {
        "id": batch.id,
        "name": batch.name,
        "numBallots": batch.num_ballots,
        "resultTallySheets": [
            {
                "name": tally_sheet.name,
                "results": {
                    result.contest_choice_id: result.result
                    for result in tally_sheet.results
                },
            }
            for tally_sheet in batch.result_tally_sheets
        ],
        "lastEditedBy": construct_batch_last_edited_by_string(batch),
    }


def construct_batch_last_edited_by_string(batch: Batch) -> Optional[str]:
    if batch.last_edited_by_support_user_email:
        return batch.last_edited_by_support_user_email
    if batch.last_edited_by_user:
        return batch.last_edited_by_user.email
    if batch.last_edited_by_tally_entry_user:
        member_1 = batch.last_edited_by_tally_entry_user.member_1
        member_2 = batch.last_edited_by_tally_entry_user.member_2
        members = []
        if member_1 is not None:
            members.append(member_1)
        if member_2 is not None:
            members.append(member_2)
        return ", ".join(members)
    return None


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches",
    methods=["GET"],
)
@restrict_access(
    [UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN, UserType.TALLY_ENTRY]
)
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
        .order_by(func.human_sort(Batch.name))
        .options(
            joinedload(Batch.result_tally_sheets).joinedload(
                BatchResultTallySheet.results
            )
        )
        .options(joinedload(Batch.last_edited_by_user))
        .options(joinedload(Batch.last_edited_by_tally_entry_user))
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


BATCH_RESULT_TALLY_SHEETS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "results": {
                "type": "object",
                "patternProperties": {"^.*$": {"type": "integer", "minimum": 0}},
            },
        },
        "required": ["name", "results"],
        "additionalProperties": False,
    },
}


def validate_batch_results(
    election: Election,
    jurisdiction: Jurisdiction,
    round: Round,
    batch: Batch,
    batch_results: List[JSONDict],
):
    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(f"Round {round.round_num} is not the current round")

    if (
        BatchResultsFinalized.query.filter_by(
            jurisdiction_id=jurisdiction.id, round_id=round.id
        ).one_or_none()
        is not None
    ):
        raise Conflict("Results have already been finalized")

    if any(draw.round_id != current_round.id for draw in batch.draws):
        raise Conflict("Batch was already audited in a previous round")

    validate(batch_results, BATCH_RESULT_TALLY_SHEETS_SCHEMA)

    # We only support one contest for batch audits
    assert len(list(jurisdiction.contests)) == 1
    contest = list(jurisdiction.contests)[0]
    contest_choice_ids = {choice.id for choice in contest.choices}

    for tally_sheet in batch_results:
        if tally_sheet["results"].keys() != contest_choice_ids:
            raise BadRequest("Invalid choice ids")

    duplicate_tally_sheet_name = find_first_duplicate(
        [tally_sheet["name"] for tally_sheet in batch_results]
    )
    if duplicate_tally_sheet_name:
        raise BadRequest(
            f"Tally sheet names must be unique. '{duplicate_tally_sheet_name}' has already been used."
        )

    total_votes = sum(
        sum(tally_sheet["results"].values()) for tally_sheet in batch_results
    )
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
@restrict_access([UserType.JURISDICTION_ADMIN, UserType.TALLY_ENTRY])
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

    BatchResultTallySheet.query.filter_by(batch_id=batch.id).delete()
    batch.result_tally_sheets = [
        BatchResultTallySheet(
            id=str(uuid.uuid4()),
            name=tally_sheet["name"],
            results=[
                BatchResult(contest_choice_id=choice_id, result=result)
                for choice_id, result in tally_sheet["results"].items()
            ],
        )
        for tally_sheet in batch_results
    ]

    user_type, user_key = get_loggedin_user(session)
    support_user_email = get_support_user(session)
    if support_user_email:
        batch.last_edited_by_support_user_email = support_user_email
        batch.last_edited_by_user_id = None
        batch.last_edited_by_tally_entry_user_id = None
    elif user_type == UserType.JURISDICTION_ADMIN:
        user = User.query.filter_by(email=user_key).one()
        batch.last_edited_by_support_user_email = None
        batch.last_edited_by_user_id = user.id
        batch.last_edited_by_tally_entry_user_id = None
    elif user_type == UserType.TALLY_ENTRY:
        batch.last_edited_by_support_user_email = None
        batch.last_edited_by_user_id = None
        batch.last_edited_by_tally_entry_user_id = user_key

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
        .outerjoin(BatchResultTallySheet)
        .group_by(Batch.id)
        .having(func.count(BatchResultTallySheet.batch_id) == 0)
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
