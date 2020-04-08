import io, csv
from sqlalchemy import func, literal_column
from sqlalchemy.dialects.postgresql import aggregate_order_by

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


def ballot_retrieval_list(jurisdiction: Jurisdiction, round: Round) -> str:
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

    # Get previously sampled ballots as a separate query for clarity
    # (self joins are cool but they're not super clear)
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

    # Get deduped sampled ballots
    ballots = (
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallotDraw.batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallotDraw.sampled_ballot)
        .join(SampledBallot.audit_board)
        .add_entity(Batch)
        .add_entity(AuditBoard)
        .group_by(
            Batch.name,
            Batch.id,
            Batch.storage_location,
            Batch.tabulator,
            AuditBoard.name,
        )
        .group_by(SampledBallotDraw.ballot_position)
        .order_by(AuditBoard.name, Batch.name, SampledBallotDraw.ballot_position)
        .values(
            Batch.id,
            SampledBallotDraw.ballot_position,
            Batch.name,
            Batch.storage_location,
            Batch.tabulator,
            AuditBoard.name,
            func.string_agg(
                SampledBallotDraw.ticket_number,
                aggregate_order_by(
                    literal_column("','"), SampledBallotDraw.ticket_number
                ),
            ),
        )
    )

    for (
        _batch_id,
        position,
        batch_name,
        storage_location,
        tabulator,
        audit_board,
        ticket_numbers,
    ) in ballots:
        previously_audited = "Y" if (batch_name, position) in previous_ballots else "N"
        retrieval_list_writer.writerow(
            [
                batch_name,
                position,
                storage_location,
                tabulator,
                ticket_numbers,
                previously_audited,
                audit_board,
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
