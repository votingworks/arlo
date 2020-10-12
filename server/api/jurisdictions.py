from typing import Dict, Optional
import enum
from flask import jsonify
from sqlalchemy import func

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from .rounds import get_current_round
from ..util.process_file import serialize_file, serialize_file_processing
from ..util.jsonschema import JSONDict


def serialize_jurisdiction(
    election: Election, jurisdiction: Jurisdiction, round_status: Optional[JSONDict]
) -> JSONDict:
    json_jurisdiction = {
        "id": jurisdiction.id,
        "name": jurisdiction.name,
        "ballotManifest": {
            "file": serialize_file(jurisdiction.manifest_file),
            "processing": serialize_file_processing(jurisdiction.manifest_file),
            "numBallots": jurisdiction.manifest_num_ballots,
            "numBatches": jurisdiction.manifest_num_batches,
        },
        "currentRoundStatus": round_status,
    }
    if election.audit_type == AuditType.BATCH_COMPARISON:
        json_jurisdiction["batchTallies"] = {
            "file": serialize_file(jurisdiction.batch_tallies_file),
            "processing": serialize_file_processing(jurisdiction.batch_tallies_file),
        }
    if election.audit_type == AuditType.BALLOT_COMPARISON:
        json_jurisdiction["cvrs"] = {
            "file": serialize_file(jurisdiction.cvr_file),
            "processing": serialize_file_processing(jurisdiction.cvr_file),
        }
    return json_jurisdiction


class JurisdictionStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


def round_status_by_jurisdiction(
    election: Election, round: Optional[Round],
) -> Dict[str, Optional[JSONDict]]:
    if not round:
        return {j.id: None for j in election.jurisdictions}
    if election.audit_type == AuditType.BALLOT_POLLING:
        return ballot_polling_round_status(election, round)
    else:
        return batch_comparison_round_status(election, round)


def ballot_polling_round_status(
    election: Election, round: Round
) -> Dict[str, Optional[JSONDict]]:
    audit_boards_set_up = dict(
        AuditBoard.query.filter_by(round_id=round.id)
        .group_by(AuditBoard.jurisdiction_id)
        .values(AuditBoard.jurisdiction_id, func.count())
    )
    audit_boards_with_ballots_not_signed_off = (
        dict(
            AuditBoard.query.filter_by(round_id=round.id, signed_off_at=None)
            .join(SampledBallot)
            .group_by(AuditBoard.jurisdiction_id)
            .values(AuditBoard.jurisdiction_id, func.count(AuditBoard.id.distinct()))
        )
        if election.online
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
        if not election.online
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

        if election.online:
            num_not_signed_off = audit_boards_with_ballots_not_signed_off.get(
                jurisdiction_id, 0
            )
            if num_not_signed_off > 0:
                return JurisdictionStatus.IN_PROGRESS
        else:
            if jurisdiction_id not in jurisdictions_with_offline_results_recorded:
                return JurisdictionStatus.IN_PROGRESS

        return JurisdictionStatus.COMPLETE

    def num_samples_audited(jurisdiction_id: str) -> int:
        if election.online:
            return audited_sample_count_by_jurisdiction.get(jurisdiction_id, 0)
        else:
            return (
                num_samples(jurisdiction_id)
                if jurisdiction_id in jurisdictions_with_offline_results_recorded
                else 0
            )

    def num_ballots_audited(jurisdiction_id: str) -> int:
        if election.online:
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
            "numUnique": num_ballots(j.id),
            "numUniqueAudited": num_ballots_audited(j.id),
        }
        for j in election.jurisdictions
    }


def batch_comparison_round_status(
    election: Election, round: Round
) -> Dict[str, Optional[JSONDict]]:
    jurisdictions_with_audit_boards = set(
        jurisdiction_id
        for jurisdiction_id, in AuditBoard.query.filter_by(round_id=round.id).values(
            AuditBoard.jurisdiction_id.distinct()
        )
    )

    sample_count_by_jurisdiction = dict(
        SampledBatchDraw.query.filter_by(round_id=round.id)
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(
            Batch.jurisdiction_id, func.count(SampledBatchDraw.ticket_number.distinct())
        )
    )
    audited_sample_count_by_jurisdiction = dict(
        SampledBatchDraw.query.filter_by(round_id=round.id)
        .join(Batch)
        .join(BatchResult)
        .group_by(Batch.jurisdiction_id)
        .having(func.count(BatchResult.batch_id) > 0)
        .values(
            Batch.jurisdiction_id, func.count(SampledBatchDraw.ticket_number.distinct())
        )
    )

    batch_count_by_jurisdiction = dict(
        Batch.query.join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count(Batch.id.distinct()))
    )
    audited_batch_count_by_jurisdiction = dict(
        Batch.query.join(SampledBatchDraw)
        .filter_by(round_id=round.id)
        .join(BatchResult)
        .group_by(Batch.jurisdiction_id)
        .having(func.count(BatchResult.batch_id) > 0)
        .values(Batch.jurisdiction_id, func.count(Batch.id.distinct()))
    )

    def num_samples(jurisdiction_id: str) -> int:
        return sample_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_samples_audited(jurisdiction_id: str) -> int:
        return audited_sample_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_batches(jurisdiction_id: str) -> int:
        return batch_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_batches_audited(jurisdiction_id: str) -> int:
        return audited_batch_count_by_jurisdiction.get(jurisdiction_id, 0)

    # NOT_STARTED = the jurisdiction hasn’t set up any audit boards
    # IN_PROGRESS = the audit boards are set up
    # COMPLETE = all the batch results are recorded
    def status(jurisdiction_id: str) -> JurisdictionStatus:
        # Special case: jurisdictions that don't get any batches assigned are
        # COMPLETE from the get-go
        if num_samples(jurisdiction_id) == 0:
            return JurisdictionStatus.COMPLETE
        if jurisdiction_id not in jurisdictions_with_audit_boards:
            return JurisdictionStatus.NOT_STARTED
        if num_samples_audited(jurisdiction_id) < num_samples(jurisdiction_id):
            return JurisdictionStatus.IN_PROGRESS
        else:
            return JurisdictionStatus.COMPLETE

    return {
        j.id: {
            "status": status(j.id),
            "numSamples": num_samples(j.id),
            "numSamplesAudited": num_samples_audited(j.id),
            "numUnique": num_batches(j.id),
            "numUniqueAudited": num_batches_audited(j.id),
        }
        for j in election.jurisdictions
    }


@api.route("/election/<election_id>/jurisdiction", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def list_jurisdictions(election: Election):
    current_round = get_current_round(election)
    round_status = round_status_by_jurisdiction(election, current_round)

    json_jurisdictions = [
        serialize_jurisdiction(election, jurisdiction, round_status[jurisdiction.id])
        for jurisdiction in election.jurisdictions
    ]
    return jsonify({"jurisdictions": json_jurisdictions})
