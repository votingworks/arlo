from collections import Counter
import logging
from typing import Dict, List, Optional, Mapping, cast as typing_cast
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
from .shared import (
    ballot_vote_deltas,
    batch_tallies,
    batch_vote_deltas,
    cvrs_for_contest,
    get_current_round,
    is_full_hand_tally,
    sampled_ballot_interpretations_to_cvrs,
    sampled_batch_results,
)
from .ballot_manifest import hybrid_jurisdiction_total_ballots
from .contests import set_contest_metadata
from .standardized_contests import process_standardized_contests_file
from ..worker.tasks import (
    background_task,
    create_background_task,
)
from ..util.file import (
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    store_file,
    timestamp_filename,
)
from ..util.jsonschema import JSONDict
from ..util.csv_parse import (
    CSVColumnType,
    CSVValueType,
    parse_csv,
    validate_csv_mimetype,
)
from ..util.csv_download import csv_response

logger = logging.getLogger("arlo")

JURISDICTION_NAME = "Jurisdiction"
ADMIN_EMAIL = "Admin Email"
EXPECTED_NUM_BALLOTS = "Expected Number of Ballots"

JURISDICTIONS_COLUMNS = [
    CSVColumnType(JURISDICTION_NAME, CSVValueType.TEXT, unique=True),
    CSVColumnType(ADMIN_EMAIL, CSVValueType.EMAIL, unique=True),
    CSVColumnType(
        EXPECTED_NUM_BALLOTS,
        CSVValueType.NUMBER,
        required_column=False,
        allow_empty_rows=True,
    ),
]


@background_task
def process_jurisdictions_file(election_id: str):
    election = Election.query.get(election_id)
    jurisdictions_file = retrieve_file(election.jurisdictions_file.storage_path)
    jurisdictions_csv = parse_csv(jurisdictions_file, JURISDICTIONS_COLUMNS)

    # Clear existing admins.
    JurisdictionAdministration.query.filter(
        JurisdictionAdministration.jurisdiction_id.in_(
            Jurisdiction.query.filter_by(election_id=election.id)
            .with_entities(Jurisdiction.id)
            .subquery()
        )
    ).delete(synchronize_session="fetch")
    new_admins: List[JurisdictionAdministration] = []

    for row in jurisdictions_csv:
        name = row[JURISDICTION_NAME]
        email = row[ADMIN_EMAIL]
        expected_num_ballots = row.get(EXPECTED_NUM_BALLOTS)

        # Find or create the user for this jurisdiction.
        user = User.query.filter_by(email=email.lower()).one_or_none()

        if not user:
            user = User(id=str(uuid.uuid4()), email=email)
            db_session.add(user)

        # Find or create the jurisdiction by name.
        jurisdiction = Jurisdiction.query.filter_by(
            election=election, name=name
        ).one_or_none()

        if not jurisdiction:
            jurisdiction = Jurisdiction(
                id=str(uuid.uuid4()),
                election=election,
                name=name,
            )
            db_session.add(jurisdiction)

        if expected_num_ballots is not None:
            jurisdiction.expected_manifest_num_ballots = expected_num_ballots

        # Link the user to the jurisdiction as an admin.
        admin = JurisdictionAdministration(jurisdiction=jurisdiction, user=user)
        db_session.add(admin)
        new_admins.append(admin)

    jurisdictions_file.close()

    # Delete unmanaged jurisdictions.
    unmanaged_admin_id_records = (
        Jurisdiction.query.outerjoin(JurisdictionAdministration)
        .filter(
            Jurisdiction.election == election,
            JurisdictionAdministration.jurisdiction_id.is_(None),
        )
        .with_entities(Jurisdiction.id)
        .all()
    )
    unmanaged_admin_ids = [id for (id,) in unmanaged_admin_id_records]
    Jurisdiction.query.filter(Jurisdiction.id.in_(unmanaged_admin_ids)).delete(
        synchronize_session="fetch"
    )

    set_contest_metadata(election)

    # If standardized contests file already uploaded, try reprocessing the
    # standardized contests file as well, since it depends on jurisdiction names.
    if election.standardized_contests_file:
        election.standardized_contests = None
        election.standardized_contests_file.task = create_background_task(
            process_standardized_contests_file, dict(election_id=election.id)
        )


def serialize_jurisdiction(
    election: Election,
    jurisdiction: Jurisdiction,
    round_status: Optional[JSONDict],
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
        "expectedBallotManifestNumBallots": jurisdiction.expected_manifest_num_ballots,
        "currentRoundStatus": round_status,
    }

    if election.audit_type == AuditType.BATCH_COMPARISON:

        def min_num_ballots_for_contest(contest: Contest) -> int:
            assert contest.votes_allowed
            return math.ceil(
                sum(
                    tally[contest.id][choice.id]
                    for tally in typing_cast(
                        JSONDict, jurisdiction.batch_tallies
                    ).values()
                    for choice in contest.choices
                )
                / contest.votes_allowed
            )

        min_num_ballots = None
        contests = list(jurisdiction.contests)
        if jurisdiction.batch_tallies and len(contests) > 0:
            # Because a ballot can contain multiple contests, don't sum minimums across contests.
            # Just take the maximum minimum as the overall minimum.
            min_num_ballots = max(
                min_num_ballots_for_contest(contest) for contest in contests
            )

        json_jurisdiction["batchTallies"] = {
            "file": serialize_file(jurisdiction.batch_tallies_file),
            "processing": serialize_file_processing(jurisdiction.batch_tallies_file),
            "numBallots": min_num_ballots,
        }

    if election.audit_type in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        file = serialize_file(jurisdiction.cvr_file)
        processing = serialize_file_processing(jurisdiction.cvr_file)
        num_cvr_ballots = (
            CvrBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction.id)
            .count()
            if (not round_status)
            and processing
            and processing["status"] == ProcessingStatus.PROCESSED
            else None
        )
        json_jurisdiction["cvrs"] = {
            "file": file and dict(file, cvrFileType=jurisdiction.cvr_file_type),
            "processing": processing,
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
    election: Election,
    round: Optional[Round],
) -> Mapping[str, Optional[JSONDict]]:
    if not round:
        return {j.id: None for j in election.jurisdictions}
    if election.audit_type == AuditType.BATCH_COMPARISON:
        return batch_round_status(election, round)
    else:
        return ballot_round_status(election, round)


class JurisdictionAuditBoardStatus(str, enum.Enum):
    NOT_SET_UP = "NOT_SET_UP"
    IN_PROGRESS = "IN_PROGRESS"
    SIGNED_OFF = "SIGNED_OFF"


def jurisdiction_audit_board_status(
    jurisdictions: List[Jurisdiction], round: Round
) -> Dict[str, JurisdictionAuditBoardStatus]:
    audit_boards_set_up = dict(
        AuditBoard.query.filter_by(round_id=round.id)
        .group_by(AuditBoard.jurisdiction_id)
        .values(AuditBoard.jurisdiction_id, func.count())
    )
    audit_boards_with_ballots_not_signed_off = dict(
        AuditBoard.query.filter_by(round_id=round.id, signed_off_at=None)
        .join(SampledBallot)
        .group_by(AuditBoard.jurisdiction_id)
        .values(AuditBoard.jurisdiction_id, func.count(AuditBoard.id.distinct()))
    )
    return {
        jurisdiction.id: (
            JurisdictionAuditBoardStatus.NOT_SET_UP
            if audit_boards_set_up.get(jurisdiction.id, 0) == 0
            else (
                JurisdictionAuditBoardStatus.IN_PROGRESS
                if audit_boards_with_ballots_not_signed_off.get(jurisdiction.id, 0) > 0
                else JurisdictionAuditBoardStatus.SIGNED_OFF
            )
        )
        for jurisdiction in jurisdictions
    }


def ballot_round_status(election: Election, round: Round) -> Dict[str, JSONDict]:
    audit_board_status = jurisdiction_audit_board_status(
        list(election.jurisdictions), round
    )

    ballots_in_round = (
        SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round.id)
        .distinct(SampledBallot.id)
        .with_entities(SampledBallot.id)
        .subquery()
    )
    ballot_count_by_jurisdiction = dict(
        SampledBallot.query.filter(SampledBallot.id.in_(ballots_in_round))
        .join(Batch)
        .group_by(Batch.jurisdiction_id)
        .values(Batch.jurisdiction_id, func.count())
    )
    audited_ballot_count_by_jurisdiction = dict(
        SampledBallot.query.filter(SampledBallot.id.in_(ballots_in_round))
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

    full_hand_tally = is_full_hand_tally(round, election)

    # Special case: if we sampled all ballots, provide progress reports based
    # on the full hand tally results
    jurisdiction_full_hand_tally_result_totals = (
        dict(
            FullHandTallyBatchResult.query.join(Jurisdiction)
            .filter_by(election_id=election.id)
            .group_by(Jurisdiction.id)
            .values(Jurisdiction.id, func.sum(FullHandTallyBatchResult.result))
        )
        if full_hand_tally
        else {}
    )

    def num_samples(jurisdiction: Jurisdiction) -> int:
        # Special case: if we sampled all ballots, we know the number of
        # ballots from the manifest
        if full_hand_tally:
            return jurisdiction.manifest_num_ballots or 0
        return sample_count_by_jurisdiction.get(jurisdiction.id, 0)

    def num_ballots(jurisdiction: Jurisdiction) -> int:
        if full_hand_tally:
            return jurisdiction.manifest_num_ballots or 0
        return ballot_count_by_jurisdiction.get(jurisdiction.id, 0)

    # NOT_STARTED = the jurisdiction hasn’t set up any audit boards
    # IN_PROGRESS = the audit boards are set up
    # COMPLETE =
    # - if online, all of the audit boards have signed off on their ballots
    # - if offline, the offline results have been recorded for all contests
    def status(jurisdiction: Jurisdiction) -> JurisdictionStatus:
        num_sampled = num_samples(jurisdiction)

        # Special case: jurisdictions that don't get any ballots assigned are
        # COMPLETE from the get-go
        if num_sampled == 0:
            return JurisdictionStatus.COMPLETE
        if (
            audit_board_status[jurisdiction.id]
            == JurisdictionAuditBoardStatus.NOT_SET_UP
        ):
            return JurisdictionStatus.NOT_STARTED

        if election.online:
            if (
                audit_board_status[jurisdiction.id]
                == JurisdictionAuditBoardStatus.IN_PROGRESS
            ):
                return JurisdictionStatus.IN_PROGRESS
        elif full_hand_tally:
            if jurisdiction.finalized_full_hand_tally_results_at is None:
                return JurisdictionStatus.IN_PROGRESS
        else:
            if jurisdiction.id not in jurisdictions_with_offline_results_recorded:
                return JurisdictionStatus.IN_PROGRESS

        return JurisdictionStatus.COMPLETE

    def num_samples_audited(jurisdiction: Jurisdiction) -> int:
        if election.online:
            return audited_sample_count_by_jurisdiction.get(jurisdiction.id, 0)
        elif full_hand_tally:
            return jurisdiction_full_hand_tally_result_totals.get(jurisdiction.id, 0)
        else:
            return (
                num_samples(jurisdiction)
                if jurisdiction.id in jurisdictions_with_offline_results_recorded
                else 0
            )

    def num_ballots_audited(jurisdiction: Jurisdiction) -> int:
        if election.online:
            return audited_ballot_count_by_jurisdiction.get(jurisdiction.id, 0)
        elif full_hand_tally:
            return jurisdiction_full_hand_tally_result_totals.get(jurisdiction.id, 0)
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

    # Special case: when we're in a full hand tally, also add a count of batches
    # submitted.
    if full_hand_tally:
        num_batches_by_jurisdiction = dict(
            FullHandTallyBatchResult.query.join(Jurisdiction)
            .filter_by(election_id=election.id)
            .group_by(Jurisdiction.id)
            .values(
                Jurisdiction.id,
                func.count(FullHandTallyBatchResult.batch_name.distinct()),
            )
        )
        for jurisdiction_id in statuses:
            statuses[jurisdiction_id]["numBatchesAudited"] = (
                num_batches_by_jurisdiction.get(jurisdiction_id, 0)
            )

    return statuses


def batch_round_status(election: Election, round: Round) -> Dict[str, JSONDict]:
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
        .join(BatchResultTallySheet)
        .group_by(Batch.jurisdiction_id)
        .having(func.count(BatchResultTallySheet.id) > 0)
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
        .join(BatchResultTallySheet)
        .group_by(Batch.jurisdiction_id)
        .having(func.count(BatchResultTallySheet.id) > 0)
        .values(Batch.jurisdiction_id, func.count(Batch.id.distinct()))
    )

    finalized_jurisdiction_ids = {
        jurisdiction_id
        for jurisdiction_id, in BatchResultsFinalized.query.filter_by(
            round_id=round.id
        ).values(BatchResultsFinalized.jurisdiction_id)
    }

    def num_samples(jurisdiction_id: str) -> int:
        return sample_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_samples_audited(jurisdiction_id: str) -> int:
        return audited_sample_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_batches(jurisdiction_id: str) -> int:
        return batch_count_by_jurisdiction.get(jurisdiction_id, 0)

    def num_batches_audited(jurisdiction_id: str) -> int:
        return audited_batch_count_by_jurisdiction.get(jurisdiction_id, 0)

    # NOT_STARTED = the jurisdiction hasn’t audited any batches yet
    # IN_PROGRESS = the jurisdiction is auditing batches
    # COMPLETE = the batch results are finalized
    def status(jurisdiction_id: str) -> JurisdictionStatus:
        # Special case: jurisdictions that don't get any batches assigned are
        # COMPLETE from the get-go
        if num_samples(jurisdiction_id) == 0:
            return JurisdictionStatus.COMPLETE
        if num_samples_audited(jurisdiction_id) == 0:
            return JurisdictionStatus.NOT_STARTED
        if jurisdiction_id not in finalized_jurisdiction_ids:
            return JurisdictionStatus.IN_PROGRESS
        else:
            return JurisdictionStatus.COMPLETE

    return {
        jurisdiction.id: {
            "status": status(jurisdiction.id),
            "numSamples": num_samples(jurisdiction.id),
            "numSamplesAudited": num_samples_audited(jurisdiction.id),
            "numUnique": num_batches(jurisdiction.id),
            "numUniqueAudited": num_batches_audited(jurisdiction.id),
        }
        for jurisdiction in election.jurisdictions
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
        retrieve_file(election.jurisdictions_file.storage_path),
        election.jurisdictions_file.name,
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

    validate_csv_mimetype(request.files["jurisdictions"])

    jurisdictions_file = request.files["jurisdictions"]
    storage_path = store_file(
        jurisdictions_file.stream,
        f"audits/{election.id}/"
        + timestamp_filename("participating_jurisdictions", "csv"),
    )
    election.jurisdictions_file = File(
        id=str(uuid.uuid4()),
        name=jurisdictions_file.filename,  # type: ignore
        storage_path=storage_path,
        uploaded_at=datetime.datetime.now(timezone.utc),
    )
    election.jurisdictions_file.task = create_background_task(
        process_jurisdictions_file, dict(election_id=election.id)
    )

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/discrepancy-counts", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_discrepancy_counts_by_jurisdiction(election: Election):
    discrepancy_count_by_jurisdiction: Dict[str, int] = Counter()
    round = get_current_round(election)
    if not round:
        raise Conflict("Audit not started")

    if election.audit_type == AuditType.BALLOT_COMPARISON:
        ballots_in_round = (
            SampledBallot.query.join(SampledBallotDraw)
            .filter_by(round_id=round.id)
            .distinct(SampledBallot.id)
            .with_entities(SampledBallot.id)
            .subquery()
        )
        sampled_ballot_id_to_jurisdiction_id = dict(
            SampledBallot.query.filter(SampledBallot.id.in_(ballots_in_round))
            .join(Batch)
            .with_entities(SampledBallot.id, Batch.jurisdiction_id)
        )
        for contest in election.contests:
            reported_results = cvrs_for_contest(contest)
            audited_results = sampled_ballot_interpretations_to_cvrs(contest)
            for ballot_id, audited_result in audited_results.items():
                vote_deltas = ballot_vote_deltas(
                    contest,
                    reported_results.get(ballot_id),
                    audited_result["cvr"],
                )
                if vote_deltas and ballot_id in sampled_ballot_id_to_jurisdiction_id:
                    jurisdiction_id = sampled_ballot_id_to_jurisdiction_id[ballot_id]
                    discrepancy_count_by_jurisdiction[jurisdiction_id] += 1

    elif election.audit_type == AuditType.BATCH_COMPARISON:
        batch_keys_in_round = set(
            SampledBatchDraw.query.filter_by(round_id=round.id)
            .join(Batch)
            .join(Jurisdiction)
            .with_entities(Jurisdiction.name, Batch.name)
            .all()
        )
        jurisdiction_name_to_id = dict(
            Jurisdiction.query.filter_by(election_id=election.id).with_entities(
                Jurisdiction.name, Jurisdiction.id
            )
        )
        contests = list(election.contests)

        # If a batch has a discrepancy in multiple contests, the discrepancy count will be incremented
        # multiple times. In other words, the discrepancy count represents the number of batch-contest
        # pairs with discrepancies, not the number of batches with discrepancies.
        for contest in contests:
            reported_batch_results = batch_tallies(contest)
            audited_batch_results = sampled_batch_results(
                contest, include_non_rla_batches=True
            )
            for batch_key, audited_batch_result in audited_batch_results.items():
                if batch_key in batch_keys_in_round:
                    vote_deltas = batch_vote_deltas(
                        reported_batch_results[batch_key][contest.id],
                        audited_batch_result[contest.id],
                    )
                    if vote_deltas:
                        jurisdiction_name, _ = batch_key
                        jurisdiction_id = jurisdiction_name_to_id[jurisdiction_name]
                        discrepancy_count_by_jurisdiction[jurisdiction_id] += 1

    else:
        raise Conflict(
            "Discrepancy counts are only available for ballot comparison and batch comparison audits"
        )

    return jsonify(
        {
            jurisdiction.id: discrepancy_count_by_jurisdiction[jurisdiction.id]
            for jurisdiction in election.jurisdictions
        }
    )
