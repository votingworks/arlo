from typing import Dict
from collections import Counter
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict
from flask import jsonify, request


from . import api
from ..api.rounds import (
    SampleSize,
    compute_sample_ballots,
    compute_sample_batches,
    create_selected_sample_sizes_schema,
    get_current_round,
)
from ..auth.auth_helpers import UserType, restrict_access
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..worker.tasks import (
    background_task,
    create_background_task,
    serialize_background_task,
)
from ..util.get_json import safe_get_json_dict


@background_task
def compute_sample_preview(election_id: str, sample_sizes: Dict[str, SampleSize]):
    election = Election.query.get(election_id)
    contest_sample_sizes = [
        (Contest.query.get(contest_id), sample_size)
        for contest_id, sample_size in sample_sizes.items()
    ]

    if election.audit_type == AuditType.BATCH_COMPARISON:
        sample_batch_draws = compute_sample_batches(election, 1, contest_sample_sizes)
        sample_draw_batch_ids = [
            batch_draw["batch_id"] for batch_draw in sample_batch_draws
        ]
        unique_sample_batch_ids = list(set(sample_draw_batch_ids))

    else:
        if election.audit_type in [
            AuditType.BALLOT_POLLING,
            AuditType.BALLOT_COMPARISON,
        ]:
            sample_ballot_draws = compute_sample_ballots(election, contest_sample_sizes)
        else:
            assert election.audit_type == AuditType.HYBRID
            cvrs_sample = compute_sample_ballots(
                election, contest_sample_sizes, filter_has_cvrs=True
            )
            no_cvrs_sample = compute_sample_ballots(
                election, contest_sample_sizes, filter_has_cvrs=False
            )
            sample_ballot_draws = cvrs_sample + no_cvrs_sample

        sample_draw_batch_ids = [
            ballot_draw["batch_id"] for ballot_draw in sample_ballot_draws
        ]
        unique_sample_ballots = set(
            (ballot_draw["batch_id"], ballot_draw["ballot_position"])
            for ballot_draw in sample_ballot_draws
        )
        unique_sample_batch_ids = [batch_id for batch_id, _ in unique_sample_ballots]

    batch_id_to_jurisdiction_id = dict(
        Batch.query.filter(Batch.id.in_(unique_sample_batch_ids))
        .join(Jurisdiction)
        .with_entities(Batch.id, Jurisdiction.id)
        .all()
    )

    sample_draw_counts_by_jurisdiction = Counter(
        batch_id_to_jurisdiction_id[batch_id] for batch_id in sample_draw_batch_ids
    )
    unique_sample_counts_by_jurisdiction = Counter(
        batch_id_to_jurisdiction_id[batch_id] for batch_id in unique_sample_batch_ids
    )

    election.sample_preview = [
        {
            "name": jurisdiction.name,
            "numSamples": sample_draw_counts_by_jurisdiction[jurisdiction.id],
            "numUnique": unique_sample_counts_by_jurisdiction[jurisdiction.id],
        }
        for jurisdiction in election.jurisdictions
    ]


def create_sample_preview_schema(audit_type: AuditType):
    return {
        "type": "object",
        "properties": {"sampleSizes": create_selected_sample_sizes_schema(audit_type)},
        "additionalProperties": False,
        "required": ["sampleSizes"],
    }


@api.route("/election/<election_id>/sample-preview", methods=["POST"])
@restrict_access([UserType.AUDIT_ADMIN])
def start_computing_sample_preview(election: Election):
    if get_current_round(election) is not None:
        raise BadRequest("Preview not allowed after audit launch")
    if election.sample_preview_task and not election.sample_preview_task.completed_at:
        raise Conflict("Arlo is already computing a sample preview.")

    json_preview_args = safe_get_json_dict(request)
    validate(
        json_preview_args,
        create_sample_preview_schema(AuditType(election.audit_type)),
    )

    election.sample_preview = None
    election.sample_preview_task = create_background_task(
        compute_sample_preview,
        dict(election_id=election.id, sample_sizes=json_preview_args["sampleSizes"]),
    )
    db_session.commit()
    return jsonify(status="ok")


@api.route("/election/<election_id>/sample-preview", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_sample_preview(election: Election):
    return jsonify(
        jurisdictions=election.sample_preview,
        task=serialize_background_task(election.sample_preview_task),
    )
