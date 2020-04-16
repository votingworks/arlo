import io, csv
from sqlalchemy import func, literal_column
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import aggregate_order_by
from flask import jsonify

from arlo_server import app
from arlo_server.auth import with_jurisdiction_access
from arlo_server.models import (
    Election,
    SampledBallotDraw,
    Round,
    Batch,
    AuditBoard,
    SampledBallot,
    Jurisdiction,
)
from util.csv_download import csv_response, election_timestamp_name
from util.jsonschema import JSONDict


def ballot_retrieval_list(jurisdiction: Jurisdiction, round: Round) -> str:
    previous_ballots_query = (
        SampledBallotDraw.query.join(SampledBallotDraw.round)
        .filter(Round.round_num < round.round_num)
        .join(SampledBallotDraw.batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .values(Batch.name, SampledBallotDraw.ballot_position)
    )
    previous_ballots = {
        (batch_name, ballot_position)
        for batch_name, ballot_position in previous_ballots_query
    }

    ballots = (
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallotDraw.batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallotDraw.sampled_ballot)
        .join(SampledBallot.audit_board)
        .group_by(AuditBoard.id, Batch.id, SampledBallotDraw.ballot_position)
        .order_by(AuditBoard.name, Batch.name, SampledBallotDraw.ballot_position)
        .values(
            Batch.name,
            SampledBallotDraw.ballot_position,
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


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/retrieval-list",
    methods=["GET"],
)
@with_jurisdiction_access
def get_retrieval_list(election: Election, jurisdiction: Jurisdiction, round_id: str):
    round = Round.query.get_or_404(round_id)
    retrieval_list_csv = ballot_retrieval_list(jurisdiction, round)
    return csv_response(
        retrieval_list_csv,
        filename=f"ballot-retrieval-{election_timestamp_name(election)}",
    )


def serialize_ballot_draw(ballot_draw: SampledBallotDraw) -> JSONDict:
    # TODO separate status for ballots that were skipped by the audit board
    ballot = ballot_draw.sampled_ballot
    audit_board = ballot.audit_board
    batch = ballot_draw.batch
    return {
        "ticketNumber": ballot_draw.ticket_number,
        "status": "AUDITED" if ballot.vote is not None else None,
        "vote": ballot.vote,
        "comment": ballot.comment,
        "position": ballot.ballot_position,
        "batch": {"id": batch.id, "name": batch.name, "tabulator": batch.tabulator,},
        "auditBoard": {"id": audit_board.id, "name": audit_board.name,},
    }


@app.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballot-draws",
    methods=["GET"],
)
@with_jurisdiction_access
def list_ballot_draws_for_jurisdiction(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round_id: str,
):
    Round.query.get_or_404(round_id)
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallot)
        .join(AuditBoard)
        .order_by(
            AuditBoard.name,
            Batch.name,
            SampledBallotDraw.ballot_position,
            SampledBallotDraw.ticket_number,
        )
        .options(
            joinedload(SampledBallotDraw.batch),
            joinedload(SampledBallotDraw.sampled_ballot).joinedload(
                SampledBallot.audit_board
            ),
        )
        .all()
    )
    json_ballot_draws = [serialize_ballot_draw(b) for b in ballot_draws]
    return jsonify({"ballotDraws": json_ballot_draws})
