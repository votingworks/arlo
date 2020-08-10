from typing import List, Dict, Optional
import enum
from flask import jsonify
from sqlalchemy import func

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access
from .rounds import get_current_round
from ..util.process_file import serialize_file, serialize_file_processing
from ..util.jsonschema import JSONDict


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


class JurisdictionStatus(str, enum.Enum):
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
    audit_boards_signed_off = (
        dict(
            AuditBoard.query.filter_by(round_id=round.id)
            .filter(AuditBoard.signed_off_at.isnot(None))
            .group_by(AuditBoard.jurisdiction_id)
            .values(AuditBoard.jurisdiction_id, func.count())
        )
        if online
        else {}
    )

    ballots_in_round = (
        SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round.id)
        .distinct(SampledBallot.id)
        .subquery()
    )
    ballot_count_by_jurisdiction = dict(
        SampledBallot.query.join(
            ballots_in_round, SampledBallot.id == ballots_in_round.columns.id
        )
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )
    audited_ballot_count_by_jurisdiction = dict(
        SampledBallot.query.join(
            ballots_in_round, SampledBallot.id == ballots_in_round.columns.id
        )
        .filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count(SampledBallot.id))
    )

    sample_count_by_jurisdiction = dict(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )
    audited_sample_count_by_jurisdiction = dict(
        SampledBallotDraw.query.filter_by(round_id=round.id)
        .join(SampledBallot)
        .filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )

    # Since we require that JAs record results for all contests at once, we
    # only need to check if any JurisdictionResult exists to know if all
    # results have been recorded.
    jurisdictions_with_offline_results_recorded = (
        {
            jurisdiction_id
            for jurisdiction_id, in (
                JurisdictionResult.query.filter_by(round_id=round.id)
                .group_by(JurisdictionResult.jurisdiction_id)
                .values(JurisdictionResult.jurisdiction_id)
            )
        }
        if not online
        else {}
    )

    def num_samples(jurisdiction_id: str) -> int:
        return sample_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_ballots(jurisdiction_id: str) -> int:
        return ballot_count_by_jurisdiction.get(jurisdiction_id, 0)

    # NOT_STARTED = the jurisdiction hasn’t set up any audit boards
    # IN_PROGRESS = the audit boards are set up
    # COMPLETE =
    # - if online, all of the audit boards have signed off on their ballots
    # - if offline, the offline results have been recorded for all contests
    def status(jurisdiction_id: str) -> JurisdictionStatus:
        num_set_up = audit_boards_set_up.get(jurisdiction_id, 0)
        num_sampled = num_samples(jurisdiction_id)

        # Special case: jurisdictions that don't get any ballots assigned are
        # COMPLETE from the get-go
        if num_sampled == 0:
            return JurisdictionStatus.COMPLETE
        if num_set_up == 0:
            return JurisdictionStatus.NOT_STARTED

        if online:
            num_signed_off = audit_boards_signed_off.get(jurisdiction_id, 0)
            if num_signed_off != num_set_up:
                return JurisdictionStatus.IN_PROGRESS
        else:
            if jurisdiction_id not in jurisdictions_with_offline_results_recorded:
                return JurisdictionStatus.IN_PROGRESS

        return JurisdictionStatus.COMPLETE

    def num_samples_audited(jurisdiction_id: str) -> int:
        if online:
            return audited_sample_count_by_jurisdiction.get(jurisdiction_id, 0)
        else:
            return (
                num_samples(jurisdiction_id)
                if jurisdiction_id in jurisdictions_with_offline_results_recorded
                else 0
            )

    def num_ballots_audited(jurisdiction_id: str) -> int:
        if online:
            return audited_ballot_count_by_jurisdiction.get(jurisdiction_id, 0)
        else:
            return (
                num_ballots(jurisdiction_id)
                if jurisdiction_id in jurisdictions_with_offline_results_recorded
                else 0
            )

    return {
        j.id: {
            "status": status(j.id),
            "numSamples": num_samples(j.id),
            "numSamplesAudited": num_samples_audited(j.id),
            "numBallots": num_ballots(j.id),
            "numBallotsAudited": num_ballots_audited(j.id),
        }
        for j in jurisdictions
    }


@api.route("/election/<election_id>/jurisdiction", methods=["GET"])
@with_election_access
def list_jurisdictions(election: Election):
    current_round = get_current_round(election)
    round_status = round_status_by_jurisdiction(
        current_round, list(election.jurisdictions), election.online
    )

    json_jurisdictions = [
        serialize_jurisdiction(j, round_status[j.id]) for j in election.jurisdictions
    ]
    return jsonify({"jurisdictions": json_jurisdictions})
