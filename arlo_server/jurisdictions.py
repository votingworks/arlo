from flask import jsonify
from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy import func

from arlo_server import app
from arlo_server.models import (
    Election,
    Jurisdiction,
    SampledBallotDraw,
    SampledBallot,
    BallotStatus,
    Batch,
    Round,
    AuditBoard,
)
from arlo_server.auth import with_election_access
from arlo_server.rounds import get_current_round
from util.process_file import serialize_file, serialize_file_processing
from util.jsonschema import JSONDict


def serialize_jurisdiction(
    jurisdiction: Jurisdiction, round_status: Optional[JSONDict]
) -> JSONDict:
    return {
        "id": jurisdiction.id,
        "name": jurisdiction.name,
        "ballotManifest": {
            "file": serialize_file(jurisdiction.manifest_file)
            if jurisdiction.manifest_file
            else None,
            "processing": serialize_file_processing(jurisdiction.manifest_file)
            if jurisdiction.manifest_file
            else None,
            "numBallots": jurisdiction.manifest_num_ballots,
            "numBatches": jurisdiction.manifest_num_batches,
        },
        "currentRoundStatus": round_status,
    }


class JurisdictionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


def round_status_by_jurisdiction(
    round: Optional[Round], jurisdictions: List[Jurisdiction], online: bool
) -> Dict[str, Optional[JSONDict]]:
    if not round:
        return {j.id: None for j in jurisdictions}

    audit_boards_set_up = dict(
        AuditBoard.query.filter_by(round_id=round.id)
        .group_by(AuditBoard.jurisdiction_id)
        .values(AuditBoard.jurisdiction_id, func.count())
    )
    audit_boards_signed_off = dict(
        AuditBoard.query.filter_by(round_id=round.id)
        .filter(AuditBoard.signed_off_at.isnot(None))
        .group_by(AuditBoard.jurisdiction_id)
        .values(AuditBoard.jurisdiction_id, func.count())
    )

    sampled_ballot_count_by_jurisdiction = dict(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )
    audited_ballot_count_by_jurisdiction = dict(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )

    def num_ballots_sampled(jurisdiction_id: str) -> int:
        return sampled_ballot_count_by_jurisdiction.get(jurisdiction_id, 0)

    # NOT_STARTED = the jurisdiction hasn’t set up any audit boards
    # IN_PROGRESS = the audit boards are set up
    # COMPLETE = all of the audit boards have signed off on their ballots
    def status(jurisdiction_id: str) -> JurisdictionStatus:
        num_set_up = audit_boards_set_up.get(jurisdiction_id, 0)
        num_signed_off = audit_boards_signed_off.get(jurisdiction_id, 0)
        num_sampled = num_ballots_sampled(jurisdiction_id)

        # Special case: jurisdictions that don't get any ballots assigned are
        # COMPLETE from the get-go
        if num_sampled == 0:
            return JurisdictionStatus.COMPLETE
        elif num_set_up == 0:
            return JurisdictionStatus.NOT_STARTED
        elif num_signed_off != num_set_up:
            return JurisdictionStatus.IN_PROGRESS
        else:
            return JurisdictionStatus.COMPLETE

    def num_ballots_audited(jurisdiction_id: str) -> int:
        if online:
            return audited_ballot_count_by_jurisdiction.get(jurisdiction_id, 0)
        else:
            # For offline audits, we can't track incremental progress on
            # auditing ballots, so we just report 0 ballots until the round is
            # complete, then report all the sampled ballots.
            return (
                0
                if status(jurisdiction_id) != JurisdictionStatus.COMPLETE
                else num_ballots_sampled(jurisdiction_id)
            )

    return {
        j.id: {
            "status": status(j.id),
            "numBallotsSampled": num_ballots_sampled(j.id),
            "numBallotsAudited": num_ballots_audited(j.id),
        }
        for j in jurisdictions
    }


@app.route("/election/<election_id>/jurisdiction", methods=["GET"])
@with_election_access
def list_jurisdictions(election: Election):
    current_round = get_current_round(election)
    round_status = round_status_by_jurisdiction(
        current_round, election.jurisdictions, election.online
    )

    json_jurisdictions = [
        serialize_jurisdiction(j, round_status[j.id]) for j in election.jurisdictions
    ]
    return jsonify({"jurisdictions": json_jurisdictions})
