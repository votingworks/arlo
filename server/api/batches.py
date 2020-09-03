import io, csv
from flask import jsonify

from . import api
from ..auth import with_jurisdiction_access
from ..models import *  # pylint: disable=wildcard-import
from ..util.csv_download import csv_response, election_timestamp_name
from ..util.jsonschema import JSONDict


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/batches/retrieval-list",
    methods=["GET"],
)
@with_jurisdiction_access
def get_batch_retrieval_list(
    election: Election, jurisdiction: Jurisdiction, round_id: str
):
    get_or_404(Round, round_id)
    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round_id)
        .join(AuditBoard)
        .group_by(AuditBoard.id, Batch.id)
        .order_by(AuditBoard.name, Batch.name)
        .values(Batch.name, Batch.storage_location, Batch.tabulator, AuditBoard.name,)
    )
    retrieval_list_rows = [
        [
            "Batch Name",
            "Storage Location",
            "Tabulator",
            "Already Audited",  # TODO implement this column
            "Audit Board",
        ]
    ] + [
        [batch_name, storage_location, tabulator, "", audit_board_name,]
        for (batch_name, storage_location, tabulator, audit_board_name,) in batches
    ]

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
    get_or_404(Round, round_id)
    batches = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBatchDraw)
        .filter_by(round_id=round_id)
        .outerjoin(AuditBoard)
        .order_by(AuditBoard.name, Batch.name)
        .all()
    )
    return jsonify({"batches": [serialize_batch(batch) for batch in batches]})
