from typing import Dict, Optional, Mapping, cast as typing_cast
import enum
import uuid
import datetime
import math
from flask import jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Conflict, BadRequest

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from ..auth import restrict_access, UserType
from .rounds import get_current_round, sampled_all_ballots
from .ballot_manifest import hybrid_jurisdiction_total_ballots
from ..util.process_file import serialize_file, serialize_file_processing
from ..util.jsonschema import JSONDict
from ..util.csv_parse import decode_csv_file
from ..util.csv_download import csv_response


def serialize_jurisdiction(
    election: Election, jurisdiction: Jurisdiction, round_status: Optional[JSONDict]
) -> JSONDict:
    json_jurisdiction: JSONDict = {
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
        num_ballots = None
        if jurisdiction.batch_tallies and len(list(election.contests)) == 1:
            contest = list(election.contests)[0]
            assert contest.votes_allowed
            num_ballots = math.ceil(
                sum(
                    tally[contest.id][choice.id]
                    for tally in typing_cast(
                        JSONDict, jurisdiction.batch_tallies
                    ).values()
                    for choice in contest.choices
                )
                / contest.votes_allowed
            )
        json_jurisdiction["batchTallies"] = {
            "file": serialize_file(jurisdiction.batch_tallies_file),
            "processing": serialize_file_processing(jurisdiction.batch_tallies_file),
            "numBallots": num_ballots,
        }

    if election.audit_type in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        processing = serialize_file_processing(jurisdiction.cvr_file)
        num_cvr_ballots = (
            CvrBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction.id)
            .count()
            if processing and processing["status"] == ProcessingStatus.PROCESSED
            else None
        )
        json_jurisdiction["cvrs"] = {
            "file": serialize_file(jurisdiction.cvr_file),
            "processing": serialize_file_processing(jurisdiction.cvr_file),
            "numBallots": num_cvr_ballots,
        }

    if election.audit_type == AuditType.HYBRID:
        ballot_counts = (
            hybrid_jurisdiction_total_ballots(jurisdiction)
            if json_jurisdiction["ballotManifest"]["processing"]
            and json_jurisdiction["ballotManifest"]["processing"]["status"]
            == ProcessingStatus.PROCESSED
            else None
        )
        json_jurisdiction["ballotManifest"]["numBallotsCvr"] = (
            ballot_counts and ballot_counts.cvr
        )
        json_jurisdiction["ballotManifest"]["numBallotsNonCvr"] = (
            ballot_counts and ballot_counts.non_cvr
        )

    return json_jurisdiction


class JurisdictionStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


def round_status_by_jurisdiction(
    election: Election, round: Optional[Round],
) -> Mapping[str, Optional[JSONDict]]:
    if not round:
        return {j.id: None for j in election.jurisdictions}
    if election.audit_type == AuditType.BATCH_COMPARISON:
        return batch_round_status(election, round)
    else:
        return ballot_round_status(election, round)


def ballot_round_status(election: Election, round: Round) -> Dict[str, JSONDict]:
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

    did_sample_all_ballots = sampled_all_ballots(round, election)

    # Special case: if we sampled all ballots, provide progress reports based
    # on the offline batch results
    jurisdiction_offline_batch_result_totals = (
        dict(
            OfflineBatchResult.query.join(Jurisdiction)
            .filter_by(election_id=election.id)
            .group_by(Jurisdiction.id)
            .values(Jurisdiction.id, func.sum(OfflineBatchResult.result))
        )
        if did_sample_all_ballots
        else {}
    )

    def num_samples(jurisdiction: Jurisdiction) -> int:
        # Special case: if we sampled all ballots, we know the number of
        # ballots from the manifest
        if did_sample_all_ballots:
            return jurisdiction.manifest_num_ballots or 0
        return sample_count_by_jurisdiction.get(jurisdiction.id, 0)

    def num_ballots(jurisdiction: Jurisdiction) -> int:
        if did_sample_all_ballots:
            return jurisdiction.manifest_num_ballots or 0
        return ballot_count_by_jurisdiction.get(jurisdiction.id, 0)

    # NOT_STARTED = the jurisdiction hasn’t set up any audit boards
    # IN_PROGRESS = the audit boards are set up
    # COMPLETE =
    # - if online, all of the audit boards have signed off on their ballots
    # - if offline, the offline results have been recorded for all contests
    def status(jurisdiction: Jurisdiction) -> JurisdictionStatus:
        num_set_up = audit_boards_set_up.get(jurisdiction.id, 0)
        num_sampled = num_samples(jurisdiction)

        # Special case: jurisdictions that don't get any ballots assigned are
        # COMPLETE from the get-go
        if num_sampled == 0:
            return JurisdictionStatus.COMPLETE
        if num_set_up == 0:
            return JurisdictionStatus.NOT_STARTED

        if election.online:
            num_not_signed_off = audit_boards_with_ballots_not_signed_off.get(
                jurisdiction.id, 0
            )
            if num_not_signed_off > 0:
                return JurisdictionStatus.IN_PROGRESS
        elif did_sample_all_ballots:
            if jurisdiction.finalized_offline_batch_results_at is None:
                return JurisdictionStatus.IN_PROGRESS
        else:
            if jurisdiction.id not in jurisdictions_with_offline_results_recorded:
                return JurisdictionStatus.IN_PROGRESS

        return JurisdictionStatus.COMPLETE

    def num_samples_audited(jurisdiction: Jurisdiction) -> int:
        if election.online:
            return audited_sample_count_by_jurisdiction.get(jurisdiction.id, 0)
        elif did_sample_all_ballots:
            return jurisdiction_offline_batch_result_totals.get(jurisdiction.id, 0)
        else:
            return (
                num_samples(jurisdiction)
                if jurisdiction.id in jurisdictions_with_offline_results_recorded
                else 0
            )

    def num_ballots_audited(jurisdiction: Jurisdiction) -> int:
        if election.online:
            return audited_ballot_count_by_jurisdiction.get(jurisdiction.id, 0)
        elif did_sample_all_ballots:
            return jurisdiction_offline_batch_result_totals.get(jurisdiction.id, 0)
        else:
            return (
                num_ballots(jurisdiction)
                if jurisdiction.id in jurisdictions_with_offline_results_recorded
                else 0
            )

    statuses: Dict[str, JSONDict] = {
        jurisdiction.id: {
            "status": status(jurisdiction),
            "numSamples": num_samples(jurisdiction),
            "numSamplesAudited": num_samples_audited(jurisdiction),
            "numUnique": num_ballots(jurisdiction),
            "numUniqueAudited": num_ballots_audited(jurisdiction),
        }
        for jurisdiction in election.jurisdictions
    }

    # Special case: when all ballots sampled, also add a count of batches
    # submitted.
    if did_sample_all_ballots:
        num_batches_by_jurisdiction = dict(
            OfflineBatchResult.query.join(Jurisdiction)
            .filter_by(election_id=election.id)
            .group_by(Jurisdiction.id)
            .values(
                Jurisdiction.id, func.count(OfflineBatchResult.batch_name.distinct())
            )
        )
        for jurisdiction_id in statuses:
            statuses[jurisdiction_id][
                "numBatchesAudited"
            ] = num_batches_by_jurisdiction.get(jurisdiction_id, 0)

    return statuses


def batch_round_status(election: Election, round: Round) -> Dict[str, JSONDict]:
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

    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election.id)
        .order_by(Jurisdiction.name)
        .options(
            joinedload(Jurisdiction.manifest_file),
            joinedload(Jurisdiction.batch_tallies_file),
            joinedload(Jurisdiction.cvr_file),
        )
        .all()
    )
    json_jurisdictions = [
        serialize_jurisdiction(election, jurisdiction, round_status[jurisdiction.id])
        for jurisdiction in jurisdictions
    ]
    return jsonify({"jurisdictions": json_jurisdictions})


@api.route("/election/<election_id>/jurisdiction/file", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_jurisdictions_file(election: Election):
    return jsonify(
        file=serialize_file(election.jurisdictions_file),
        processing=serialize_file_processing(election.jurisdictions_file),
    )


@api.route("/election/<election_id>/jurisdiction/file/csv", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def download_jurisdictions_file(election: Election):
    if not election.jurisdictions_file:
        return NotFound()

    return csv_response(
        election.jurisdictions_file.contents, election.jurisdictions_file.name
    )


JURISDICTION_NAME = "Jurisdiction"
ADMIN_EMAIL = "Admin Email"


@api.route("/election/<election_id>/jurisdiction/file", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def update_jurisdictions_file(election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update jurisdictions after audit has started.")

    if "jurisdictions" not in request.files:
        raise BadRequest("Missing required file parameter 'jurisdictions'")

    jurisdictions_file = request.files["jurisdictions"]
    election.jurisdictions_file = File(
        id=str(uuid.uuid4()),
        name=jurisdictions_file.filename,
        contents=decode_csv_file(jurisdictions_file),
        uploaded_at=datetime.datetime.now(timezone.utc),
    )

    db_session.commit()

    return jsonify(status="ok")
