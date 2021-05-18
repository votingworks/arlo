import uuid
from collections import defaultdict
from typing import (
    Optional,
    NamedTuple,
    List,
    Tuple,
    Dict,
    cast as typing_cast,
    TypedDict,
)
from datetime import datetime
from flask import jsonify, request
from jsonschema import validate
from werkzeug.exceptions import BadRequest, Conflict
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from . import sample_sizes as sample_sizes_module
from ..util.isoformat import isoformat
from ..util.group_by import group_by
from ..util.jsonschema import JSONDict
from ..audit_math import (
    sampler,
    ballot_polling,
    macro,
    supersimple,
    sampler_contest,
    suite,
)
from .cvrs import hybrid_contest_choice_vote_counts, cvr_contests_metadata
from .ballot_manifest import hybrid_contest_total_ballots
from ..worker.tasks import (
    background_task,
    create_background_task,
    serialize_background_task,
)
from ..activity_log import (
    record_activity,
    activity_base,
    StartRound,
    EndRound,
)


def get_current_round(election: Election) -> Optional[Round]:
    if len(list(election.rounds)) == 0:
        return None
    return max(election.rounds, key=lambda r: r.round_num)


def get_previous_round(election: Election, round: Round) -> Optional[Round]:
    if round.round_num == 1:
        return None
    return next(r for r in election.rounds if r.round_num == round.round_num - 1)


def is_audit_complete(round: Round):
    if not round.ended_at:
        return None
    targeted_round_contests = (
        RoundContest.query.filter_by(round_id=round.id)
        .join(Contest)
        .filter_by(is_targeted=True)
        .all()
    )
    return all(c.is_complete for c in targeted_round_contests)


def count_audited_votes(election: Election, round: Round):
    for round_contest in round.round_contests:
        contest = round_contest.contest

        # For batch audits, count the votes for each audited Batch
        if election.audit_type == AuditType.BATCH_COMPARISON:
            vote_counts = dict(
                BatchResult.query.filter(
                    BatchResult.batch_id.in_(
                        SampledBatchDraw.query.filter_by(round_id=round.id)
                        .with_entities(SampledBatchDraw.batch_id)
                        .subquery()
                    )
                )
                .group_by(BatchResult.contest_choice_id)
                .values(BatchResult.contest_choice_id, func.sum(BatchResult.result))
            )

        # Otherwise, handle ballot polling, ballot comparison, and hybrid
        # audits. Note that we will only actually use these vote counts in the
        # p-value calculation for ballot polling audits and hybrid audits (just
        # counting the non-CVR ballot segment). In ballot comparison, we just
        # show these totals for the audit report.
        else:
            # For online audits, count the votes from each BallotInterpretation
            if election.online:
                interpretations_query = (
                    BallotInterpretation.query.filter_by(
                        contest_id=contest.id,
                        is_overvote=False,
                        interpretation=Interpretation.VOTE,
                    )
                    .join(SampledBallot)
                    .join(SampledBallotDraw)
                    .filter_by(round_id=round.id)
                    .join(BallotInterpretation.selected_choices)
                    .group_by(ContestChoice.id)
                )

                # For hybrid audits, only count the non-CVR ballots
                if election.audit_type == AuditType.HYBRID:
                    interpretations_query = interpretations_query.join(Batch).filter_by(
                        has_cvrs=False
                    )

                # For a targeted contest, count the ballot draws sampled for the contest
                if contest.is_targeted:
                    vote_counts = dict(
                        interpretations_query.filter(
                            SampledBallotDraw.contest_id == contest.id
                        ).values(ContestChoice.id, func.count())
                    )
                # For an opportunistic contest, count the unique ballots that were
                # audited for this contest, regardless of which contest they were
                # sampled for.
                else:
                    vote_counts = dict(
                        interpretations_query.values(
                            ContestChoice.id, func.count(SampledBallot.id.distinct())
                        )
                    )

            # For offline audits, sum the JurisdictionResults
            else:
                assert election.audit_type == AuditType.BALLOT_POLLING
                vote_counts = dict(
                    JurisdictionResult.query.filter_by(
                        round_id=round.id, contest_id=contest.id,
                    )
                    .group_by(JurisdictionResult.contest_choice_id)
                    .values(
                        JurisdictionResult.contest_choice_id,
                        func.sum(JurisdictionResult.result),
                    )
                )

        for contest_choice in contest.choices:
            result = RoundContestResult(
                round_id=round.id,
                contest_id=contest.id,
                contest_choice_id=contest_choice.id,
                result=vote_counts.get(contest_choice.id, 0),
            )
            db_session.add(result)


def contest_results_by_round(contest: Contest) -> Optional[Dict[str, Dict[str, int]]]:
    results_by_round: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for result in contest.results:
        results_by_round[result.round_id][result.contest_choice_id] = result.result
    return results_by_round if len(results_by_round) > 0 else None


# { batch_key: { contest_id: { choice_id: votes }}}
BatchTallies = Dict[Tuple[str, str], Dict[str, Dict[str, int]]]


def batch_tallies(election: Election) -> BatchTallies:
    # We only support one contest for batch audits
    assert len(list(election.contests)) == 1
    contest = list(election.contests)[0]

    # Key each batch by jurisdiction name and batch name since batch names
    # are only guaranteed unique within a jurisdiction
    return {
        (jurisdiction.name, batch_name): tally
        for jurisdiction in contest.jurisdictions
        for batch_name, tally in jurisdiction.batch_tallies.items()  # type: ignore
    }


def sampled_batch_results(election: Election,) -> BatchTallies:
    results_by_batch_and_choice = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .join(SampledBatchDraw)
        .join(Jurisdiction.contests)
        .join(ContestChoice)
        .outerjoin(
            BatchResult,
            and_(
                BatchResult.batch_id == Batch.id,
                BatchResult.contest_choice_id == ContestChoice.id,
            ),
        )
        .distinct(Jurisdiction.id, Batch.id, ContestChoice.id)
        .values(
            Jurisdiction.name,
            Batch.name,
            ContestChoice.id,
            func.coalesce(BatchResult.result, 0),
        )
    )
    results_by_batch = group_by(
        results_by_batch_and_choice,
        key=lambda result: (result[0], result[1]),  # (jurisdiction_name, batch_name)
    )
    # We only support one contest for batch audits
    assert len(list(election.contests)) == 1
    contest_id = list(election.contests)[0].id
    return {
        batch_key: {
            contest_id: {
                choice_id: result for (_, _, choice_id, result) in batch_results
            }
        }
        for batch_key, batch_results in results_by_batch.items()
    }


def batches_times_sampled(election: Election) -> Dict[Tuple[str, str], int]:
    sampled_batch_draw_counts = (
        SampledBatchDraw.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .group_by(Jurisdiction.name, Batch.name)
        .values(Jurisdiction.name, Batch.name, func.count())
    )
    return {
        (jurisdiction_name, batch_name): count
        for jurisdiction_name, batch_name, count in sampled_batch_draw_counts
    }


def round_sizes(contest: Contest) -> Dict[int, int]:
    return dict(
        Round.query.join(SampledBallotDraw)
        .filter_by(contest_id=contest.id)
        .group_by(Round.id)
        .values(Round.round_num, func.count(SampledBallotDraw.ticket_number))
    )


def cvrs_for_contest(contest: Contest) -> sampler_contest.CVRS:
    choice_name_to_id = {choice.name: choice.id for choice in contest.choices}

    cvrs: sampler_contest.CVRS = {}

    for jurisdiction in contest.jurisdictions:
        metadata = cvr_contests_metadata(jurisdiction)
        assert metadata is not None
        choices_metadata = metadata[contest.name]["choices"]

        interpretations_by_ballot = (
            CvrBallot.query.join(Batch)
            .filter_by(jurisdiction_id=jurisdiction.id)
            .join(
                SampledBallot,
                and_(
                    CvrBallot.batch_id == SampledBallot.batch_id,
                    CvrBallot.ballot_position == SampledBallot.ballot_position,
                ),
            )
            .values(SampledBallot.id, CvrBallot.interpretations)
        )

        for ballot_key, interpretations_str in interpretations_by_ballot:
            ballot_cvr: sampler_contest.CVR = {contest.id: {}}
            # interpretations is the raw CVR string: 1,0,0,1,0,1,0. We need to
            # pick out the interpretation for each contest choice. We saved the
            # column index for each choice when we parsed the CVR.
            interpretations = interpretations_str.split(",")
            for choice_name, choice_metadata in choices_metadata.items():
                interpretation = interpretations[choice_metadata["column"]]
                # If the interpretations are empty, it means the contest wasn't
                # on the ballot, so we should skip this contest entirely for
                # this ballot.
                if interpretation == "":
                    ballot_cvr = {}
                else:
                    choice_id = choice_name_to_id[choice_name]
                    ballot_cvr[contest.id][choice_id] = int(interpretation)

            cvrs[ballot_key] = ballot_cvr

    return cvrs


def sampled_ballot_interpretations_to_cvrs(
    contest: Contest,
) -> sampler_contest.SAMPLECVRS:
    ballots_query = SampledBallot.query.join(Batch)

    # In hybrid audits, only count CVR ballots
    if contest.election.audit_type == AuditType.HYBRID:
        ballots_query = ballots_query.filter(
            Batch.has_cvrs == True  # pylint: disable=singleton-comparison
        )

    # For targeted contests, count the number of times the ballot was sampled
    if contest.is_targeted:
        ballots_query = (
            ballots_query.join(SampledBallotDraw)
            .filter_by(contest_id=contest.id)
            .group_by(SampledBallot.id)
            .with_entities(SampledBallot, func.count(SampledBallotDraw.ticket_number))
        )
    # For opportunistic contests, we say each ballot was only sampled once
    else:
        ballots_query = (
            ballots_query.join(Jurisdiction)
            .join(Jurisdiction.contests)
            .filter_by(id=contest.id)
            .with_entities(SampledBallot, literal(1))
        )

    ballots = ballots_query.options(
        joinedload(SampledBallot.interpretations)
        .joinedload(BallotInterpretation.selected_choices)
        .load_only(ContestChoice.id)
    ).all()

    # The CVR we build should have a 1 for each choice that got voted for,
    # and a 0 otherwise. There are a couple special cases:
    # - Contest wasn't on the ballot - CVR should be an empty object
    # - Audit board couldn't find the ballot - CVR should be None
    cvrs: sampler_contest.SAMPLECVRS = {}
    for ballot, times_sampled in ballots:
        if ballot.status == BallotStatus.NOT_FOUND:
            cvrs[ballot.id] = {"times_sampled": times_sampled, "cvr": None}

        elif ballot.status == BallotStatus.AUDITED:
            interpretation = next(
                (
                    interpretation
                    for interpretation in ballot.interpretations
                    if interpretation.contest_id == contest.id
                ),
                None,
            )
            if interpretation is None:  # Contest not on ballot
                ballot_cvr = {}
            else:
                ballot_cvr = {contest.id: {choice.id: 0 for choice in contest.choices}}
                if interpretation.interpretation == Interpretation.VOTE:
                    for choice in interpretation.selected_choices:
                        ballot_cvr[contest.id][choice.id] = 1

            cvrs[ballot.id] = {"times_sampled": times_sampled, "cvr": ballot_cvr}

    return cvrs


def hybrid_contest_strata(
    contest: Contest,
) -> Tuple[suite.BallotPollingStratum, suite.BallotComparisonStratum]:
    total_ballots = hybrid_contest_total_ballots(contest)
    vote_counts = hybrid_contest_choice_vote_counts(contest)
    assert vote_counts
    non_cvr_vote_counts = {
        choice_id: vote_count.non_cvr for choice_id, vote_count in vote_counts.items()
    }
    cvr_vote_counts = {
        choice_id: vote_count.cvr for choice_id, vote_count in vote_counts.items()
    }

    # For targeted contests, count the number of samples drawn for this
    # contest so far
    if contest.is_targeted:
        num_previous_samples_dict = dict(
            SampledBallotDraw.query.filter_by(contest_id=contest.id)
            .join(SampledBallot)
            .join(Batch)
            .group_by(Batch.has_cvrs)
            .values(Batch.has_cvrs, func.count(SampledBallotDraw.ticket_number))
        )
    # For opportunistic contests, count the number of ballots in jurisdictions
    # in this contest's universe that were sampled (for some targeted contest)
    else:
        num_previous_samples_dict = dict(
            SampledBallot.query.join(Batch)
            .join(Jurisdiction)
            .join(Jurisdiction.contests)
            .filter_by(id=contest.id)
            .group_by(Batch.has_cvrs)
            .values(Batch.has_cvrs, func.count(SampledBallot.id))
        )

    non_cvr_previous_samples = num_previous_samples_dict.get(False, 0)
    cvr_previous_samples = num_previous_samples_dict.get(True, 0)

    # In hybrid audits, we only store round contest results for non-CVR
    # ballots
    non_cvr_sample_results = contest_results_by_round(contest) or {}
    non_cvr_stratum = suite.BallotPollingStratum(
        total_ballots.non_cvr,
        non_cvr_vote_counts,
        non_cvr_sample_results,
        non_cvr_previous_samples,
    )

    cvr_reported_results = cvrs_for_contest(contest)
    # The CVR sample results are filtered to only CVR ballots
    suite_contest = sampler_contest.from_db_contest(contest)
    cvr_sample_results = sampled_ballot_interpretations_to_cvrs(contest)
    cvr_misstatements = suite.misstatements(
        suite_contest, cvr_reported_results, cvr_sample_results,
    )
    # Create a stratum for CVR ballots
    cvr_stratum = suite.BallotComparisonStratum(
        total_ballots.cvr, cvr_vote_counts, cvr_misstatements, cvr_previous_samples,
    )

    return non_cvr_stratum, cvr_stratum


def calculate_risk_measurements(election: Election, round: Round):
    assert election.risk_limit is not None

    for round_contest in round.round_contests:
        contest = round_contest.contest

        if election.audit_type == AuditType.BALLOT_POLLING:
            assert election.audit_math_type is not None
            p_values, is_complete = ballot_polling.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                contest_results_by_round(contest) or {},
                AuditMathType(election.audit_math_type),
                round_sizes(contest),
            )
            p_value = max(p_values.values())
        elif election.audit_type == AuditType.BATCH_COMPARISON:
            p_value, is_complete = macro.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                batch_tallies(election),
                sampled_batch_results(election),
                batches_times_sampled(election),
            )
        elif election.audit_type == AuditType.BALLOT_COMPARISON:
            p_value, is_complete = supersimple.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                cvrs_for_contest(contest),
                sampled_ballot_interpretations_to_cvrs(contest),
            )
        else:
            assert election.audit_type == AuditType.HYBRID
            non_cvr_stratum, cvr_stratum = hybrid_contest_strata(contest)
            p_value, is_complete = suite.compute_risk(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                non_cvr_stratum,
                cvr_stratum,
            )

        round_contest.end_p_value = p_value
        round_contest.is_complete = is_complete


def end_round(election: Election, round: Round):
    count_audited_votes(election, round)
    calculate_risk_measurements(election, round)
    round.ended_at = datetime.now(timezone.utc)

    db_session.flush()  # Ensure round contest results are queryable by is_audit_complete
    record_activity(
        EndRound(
            timestamp=round.ended_at,
            base=activity_base(election),
            round_num=round.round_num,
            is_audit_complete=is_audit_complete(round),
        )
    )


def is_round_complete(election: Election, round: Round) -> bool:
    # For batch audits, check that all sampled batches have recorded results
    if election.audit_type == AuditType.BATCH_COMPARISON:
        num_batches_without_results: int = (
            Batch.query.join(SampledBatchDraw)
            .filter_by(round_id=round.id)
            .outerjoin(BatchResult)
            .group_by(Batch.id)
            .having(func.count(BatchResult.batch_id) == 0)
            .count()
        )
        return num_batches_without_results == 0

    # For online audits, check that all the audit boards are finished auditing
    if election.online:
        num_jurisdictions_without_audit_boards_set_up: int = (
            # For each jurisdiction...
            Jurisdiction.query.filter_by(election_id=election.id)
            # Where there are ballots that haven't been audited...
            .join(Jurisdiction.batches)
            .join(Batch.ballots)
            .filter(SampledBallot.status == BallotStatus.NOT_AUDITED)
            # And those ballots got sampled this round...
            .join(SampledBallot.draws)
            .filter_by(round_id=round.id)
            # Count the number of audit boards set up.
            .outerjoin(
                AuditBoard,
                and_(
                    AuditBoard.jurisdiction_id == Jurisdiction.id,
                    AuditBoard.round_id == round.id,
                ),
            )
            .group_by(Jurisdiction.id)
            # Finally, count how many jurisdictions have no audit boards set up.
            .having(func.count(AuditBoard.id) == 0)
            .count()
        )
        num_audit_boards_with_ballots_not_signed_off: int = (
            AuditBoard.query.filter_by(round_id=round.id, signed_off_at=None)
            .join(SampledBallot)
            .group_by(AuditBoard.id)
            .count()
        )
        return (
            num_jurisdictions_without_audit_boards_set_up == 0
            and num_audit_boards_with_ballots_not_signed_off == 0
        )

    # For offline audits, check that we have results recorded for every
    # jurisdiction that had ballots sampled
    else:
        num_jurisdictions_without_results: int
        # Special case: if we sampled all ballots, we just check every
        # jurisdiction in the targeted contest's universe
        if sampled_all_ballots(round, election):
            num_jurisdictions_without_results = (
                Contest.query.filter_by(election_id=election.id, is_targeted=True)
                .join(Contest.jurisdictions)
                .outerjoin(
                    JurisdictionResult,
                    and_(
                        JurisdictionResult.jurisdiction_id == Jurisdiction.id,
                        JurisdictionResult.contest_id == Contest.id,
                        JurisdictionResult.round_id == round.id,
                    ),
                )
                .group_by(Jurisdiction.id, Contest.id)
                .having(func.count(JurisdictionResult.result) == 0)
                .count()
            )
        else:
            num_jurisdictions_without_results = (
                # For each jurisdiction...
                Jurisdiction.query.filter_by(election_id=election.id)
                # Where ballots were sampled...
                .join(Jurisdiction.batches)
                .join(Batch.ballots)
                # And those ballots were sampled this round...
                .join(SampledBallot.draws)
                .filter_by(round_id=round.id)
                .join(SampledBallotDraw.contest)
                # Count the number of results recorded for each contest.
                .outerjoin(
                    JurisdictionResult,
                    and_(
                        JurisdictionResult.jurisdiction_id == Jurisdiction.id,
                        JurisdictionResult.contest_id == Contest.id,
                        JurisdictionResult.round_id == round.id,
                    ),
                )
                # Finally, count the number of jurisdiction/contest pairs for which
                # there is no result recorded
                .group_by(Jurisdiction.id, Contest.id)
                .having(func.count(JurisdictionResult.result) == 0)
                .count()
            )
        return num_jurisdictions_without_results == 0


def sampled_all_ballots(round: Round, election: Election):
    return election.audit_type == AuditType.BALLOT_POLLING and any(
        typing_cast(JSONDict, round_contest.sample_size)["size"]
        >= round_contest.contest.total_ballots_cast
        for round_contest in round.round_contests
        if round_contest.sample_size is not None
        # total_ballots_cast can't be None here, but typechecker needs this
        and round_contest.contest.total_ballots_cast is not None
    )


class SampleSize(TypedDict):
    size: int
    key: str
    prob: Optional[float]
    sizeCvr: int  # Only in hybrid audits
    sizeNonCvr: int  # Only in hybrid audits


class BallotDraw(NamedTuple):
    # ballot_key: ((jurisdiction name, batch name), ballot_position)
    ballot_key: Tuple[Tuple[str, str], int]
    contest_id: str
    ticket_number: str


@background_task
def draw_sample(round_id: str, election_id: str):
    round = Round.query.filter_by(id=round_id, election_id=election_id).one()
    election = round.election

    # For rounds after the first round, automatically select a sample size
    if round.round_num > 1:

        def select_sample_size(options):
            audit_type = AuditType(election.audit_type)
            if audit_type == AuditType.BALLOT_POLLING:
                return options.get("0.9", options.get("asn"))
            elif audit_type == AuditType.BATCH_COMPARISON:
                return options["macro"]
            elif audit_type == AuditType.BALLOT_COMPARISON:
                return options["supersimple"]
            else:
                assert audit_type == AuditType.HYBRID
                return options["suite"]

        sample_size_options = sample_sizes_module.sample_size_options(election)
        for round_contest in round.round_contests:
            if round_contest.contest_id in sample_size_options:
                round_contest.sample_size = select_sample_size(
                    sample_size_options[round_contest.contest_id]
                )

    contest_sample_sizes = [
        (round_contest.contest, round_contest.sample_size)
        for round_contest in round.round_contests
        if round_contest.sample_size
    ]

    # Special case: if we are sampling all ballots, we don't need to actually
    # draw a sample. Instead, we force an offline audit.
    if sampled_all_ballots(round, election):
        if len(contest_sample_sizes) > 1:
            raise Conflict(
                "Cannot sample all ballots when there are multiple targeted contests."
            )
        election.online = False
        return

    if election.audit_type == AuditType.BATCH_COMPARISON:
        sample_batches(election, round, contest_sample_sizes)
    elif election.audit_type in [AuditType.BALLOT_POLLING, AuditType.BALLOT_COMPARISON]:
        sample_ballots(election, round, contest_sample_sizes)
    else:
        assert election.audit_type == AuditType.HYBRID
        sample_ballots(election, round, contest_sample_sizes, filter_has_cvrs=True)
        sample_ballots(election, round, contest_sample_sizes, filter_has_cvrs=False)


def sample_ballots(
    election: Election,
    round: Round,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
    # For hybrid audits only, Batch.has_cvrs will be true/false if the batch
    # contains ballots with CVRs or not (based on the manifest).
    # filter_has_cvrs will constrain the ballots to sample based on
    # Batch.has_cvrs. Since Batch.has_cvrs is None for all other audit types,
    # the default filter is None.
    filter_has_cvrs: bool = None,
):
    participating_jurisdictions = {
        jurisdiction
        for (contest, _) in contest_sample_sizes
        for jurisdiction in contest.jurisdictions
    }

    # Audits must be deterministic and repeatable for the same real world
    # inputs. So the sampler expects the same input for the same real world
    # data. Thus, we use the jurisdiction name and batch keys
    # (deterministic real world ids) instead of the jurisdiction and batch
    # ids (non-deterministic uuids that we generate for each audit).
    batch_id_to_key = {
        batch.id: (jurisdiction.name, batch.tabulator, batch.name)
        for jurisdiction in participating_jurisdictions
        for batch in jurisdiction.batches
    }
    batch_key_to_id = {
        batch_key: batch_id for batch_id, batch_key in batch_id_to_key.items()
    }

    def draw_sample_for_contest(
        contest: Contest, sample_size: SampleSize
    ) -> List[BallotDraw]:
        # Compute the total number of ballot samples in all rounds leading up to
        # this one. Note that this corresponds to the number of SampledBallotDraws,
        # not SampledBallots.
        num_previously_sampled = (
            SampledBallotDraw.query.filter_by(contest_id=contest.id)
            .join(SampledBallot)
            .join(Batch)
            .filter_by(has_cvrs=filter_has_cvrs)
            .count()
        )

        # Create the pool of ballots to sample (aka manifest) by combining the
        # manifests from every jurisdiction in the contest's universe.
        manifest = {
            batch_id_to_key[batch.id]: list(range(1, batch.num_ballots + 1))
            for jurisdiction in contest.jurisdictions
            for batch in jurisdiction.batches
            if batch.has_cvrs == filter_has_cvrs
        }

        if filter_has_cvrs is None:
            sample_size_num = sample_size["size"]
        elif filter_has_cvrs:
            sample_size_num = sample_size["sizeCvr"]
        else:
            sample_size_num = sample_size["sizeNonCvr"]

        # Do the math! i.e. compute the actual sample
        sample = sampler.draw_sample(
            str(election.random_seed),
            dict(manifest),
            sample_size_num,
            num_previously_sampled,
            # In hybrid audits, sample without replacement for the non-CVR
            # ballots, and with replacement for the CVR ballots.
            # All other audit types sample with replacement.
            with_replacement=(True if filter_has_cvrs is None else filter_has_cvrs),
        )
        return [
            BallotDraw(
                ballot_key=ballot_key,
                contest_id=contest.id,
                ticket_number=ticket_number,
            )
            for (ticket_number, ballot_key, _) in sample
        ]

    # Draw a sample for each contest
    samples = [
        draw_sample_for_contest(contest, sample_size)
        for contest, sample_size in contest_sample_sizes
    ]

    # Group all sample draws by ballot
    sample_draws_by_ballot = group_by(
        [sample_draw for sample in samples for sample_draw in sample],
        key=lambda sample_draw: sample_draw.ballot_key,
    )

    # Record which ballots are sampled in the db.
    # Note that a ballot may be sampled more than once (within a round or
    # across multiple rounds). We create one SampledBallot for each real-world
    # ballot that gets sampled, and record each time it gets sampled with a
    # SampledBallotDraw. That way we can ensure that we don't need to actually
    # look at a real-world ballot that we've already audited, even if it gets
    # sampled again.
    for ballot_key, sample_draws in sample_draws_by_ballot.items():
        batch_key, ballot_position = ballot_key
        batch_id = batch_key_to_id[batch_key]

        sampled_ballot = SampledBallot.query.filter_by(
            batch_id=batch_id, ballot_position=ballot_position
        ).first()
        if not sampled_ballot:
            sampled_ballot = SampledBallot(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                ballot_position=ballot_position,
                status=BallotStatus.NOT_AUDITED,
            )
            db_session.add(sampled_ballot)

        for sample_draw in sample_draws:
            sampled_ballot_draw = SampledBallotDraw(
                ballot_id=sampled_ballot.id,
                round_id=round.id,
                contest_id=sample_draw.contest_id,
                ticket_number=sample_draw.ticket_number,
            )
            db_session.add(sampled_ballot_draw)


def sample_batches(
    election: Election,
    round: Round,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
):
    # We only support one contest for batch audits
    assert len(contest_sample_sizes) == 1
    contest, sample_size = contest_sample_sizes[0]

    num_previously_sampled = (
        SampledBatchDraw.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .count()
    )

    # Create a mapping from batch keys used in the sampling back to batch ids
    batches = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .values(Jurisdiction.name, Batch.name, Batch.id)
    )
    batch_key_to_id = {
        (jurisdiction_name, batch_name): batch_id
        for jurisdiction_name, batch_name, batch_id in batches
    }

    sample = sampler.draw_ppeb_sample(
        str(election.random_seed),
        sampler_contest.from_db_contest(contest),
        sample_size["size"],
        num_previously_sampled,
        batch_tallies(election),
    )

    for (ticket_number, batch_key) in sample:
        sampled_batch_draw = SampledBatchDraw(
            batch_id=batch_key_to_id[batch_key],
            round_id=round.id,
            ticket_number=ticket_number,
        )
        db_session.add(sampled_batch_draw)


def create_round_schema(audit_type: AuditType):
    return {
        "type": "object",
        "properties": {
            "roundNum": {"type": "integer", "minimum": 1,},
            "sampleSizes": {
                "type": "object",
                "patternProperties": {
                    "^.*$": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "prob": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                            **(
                                {
                                    "sizeCvr": {"type": "integer"},
                                    "sizeNonCvr": {"type": "integer"},
                                    # We ignore size in hybrid audits
                                    "size": {
                                        "anyOf": [{"type": "integer"}, {"type": "null"}]
                                    },
                                }
                                if audit_type == AuditType.HYBRID
                                else {"size": {"type": "integer"}}
                            ),
                        },
                        "additionalProperties": False,
                        "required": (
                            ["sizeCvr", "sizeNonCvr", "key", "prob"]
                            if audit_type == AuditType.HYBRID
                            else ["size", "key", "prob"]
                        ),
                    }
                },
            },
        },
        "additionalProperties": False,
        "required": ["roundNum"],
    }


# Raises if invalid
def validate_round(round: dict, election: Election):
    validate(round, create_round_schema(AuditType(election.audit_type)))

    current_round = get_current_round(election)
    if current_round and not current_round.draw_sample_task.completed_at:
        raise Conflict("Arlo is already currently drawing the sample for this round.")

    next_round_num = current_round.round_num + 1 if current_round else 1
    if round["roundNum"] != next_round_num:
        raise BadRequest(f"The next round should be round number {next_round_num}")

    if current_round and not current_round.ended_at:
        raise Conflict("The current round is not complete")


def validate_sample_size(round: dict, election: Election):
    targeted_contests = [
        contest for contest in election.contests if contest.is_targeted
    ]

    if "sampleSizes" not in round:
        raise BadRequest("Sample sizes are required for round 1")

    if set(round["sampleSizes"].keys()) != {c.id for c in targeted_contests}:
        raise BadRequest("Sample sizes provided do not match targeted contest ids")

    for contest in targeted_contests:
        sample_size = round["sampleSizes"][contest.id]
        total_batches = sum(
            jurisdiction.manifest_num_batches or 0
            for jurisdiction in contest.jurisdictions
        )
        valid_keys, max_sample_size = {
            AuditType.BALLOT_POLLING: (
                ["asn", "0.9", "0.8", "0.7", "custom", "all-ballots"],
                contest.total_ballots_cast,
            ),
            AuditType.BALLOT_COMPARISON: (
                ["supersimple", "custom"],
                contest.total_ballots_cast,
            ),
            AuditType.BATCH_COMPARISON: (["macro", "custom"], total_batches),
            AuditType.HYBRID: (["suite", "custom"], contest.total_ballots_cast),
        }[AuditType(election.audit_type)]

        if sample_size["key"] not in valid_keys:
            raise BadRequest(
                f"Invalid sample size key for contest {contest.name}: {sample_size['key']}"
            )

        if sample_size["key"] == "custom":
            if election.audit_type == AuditType.HYBRID:
                total_ballots = hybrid_contest_total_ballots(contest)
                if sample_size["sizeCvr"] > total_ballots.cvr:
                    raise BadRequest(
                        f"CVR sample size for contest {contest.name} must be less than or equal to:"
                        f" {total_ballots.cvr} (the total number of CVR ballots in the contest)"
                    )
                if sample_size["sizeNonCvr"] > total_ballots.non_cvr:
                    raise BadRequest(
                        f"Non-CVR sample size for contest {contest.name} must be less than or equal to:"
                        f" {total_ballots.non_cvr} (the total number of non-CVR ballots in the contest)"
                    )

            elif sample_size["size"] > max_sample_size:
                ballots_or_batches = (
                    "batches"
                    if election.audit_type == AuditType.BATCH_COMPARISON
                    else "ballots"
                )
                raise BadRequest(
                    f"Sample size for contest {contest.name} must be less than or equal to:"
                    f" {max_sample_size} (the total number of {ballots_or_batches} in the contest)"
                )


@api.route("/election/<election_id>/round", methods=["POST"])
@restrict_access([UserType.AUDIT_ADMIN])
def create_round(election: Election):
    json_round = request.get_json()
    validate_round(json_round, election)

    round = Round(
        id=str(uuid.uuid4()), election_id=election.id, round_num=json_round["roundNum"],
    )
    db_session.add(round)

    # For round 1, use the given sample size for each contest. In later rounds,
    # we'll select a sample size automatically when drawing the sample.
    sample_sizes = {}
    if json_round["roundNum"] == 1:
        validate_sample_size(json_round, election)
        sample_sizes = json_round["sampleSizes"]

    # Figure out which contests still need auditing
    previous_round = get_previous_round(election, round)
    contests_that_havent_met_risk_limit = (
        [
            round_contest.contest
            for round_contest in previous_round.round_contests
            if not round_contest.is_complete
        ]
        if previous_round
        else election.contests
    )

    # Create RoundContest objects to include the contests in this round
    round.round_contests = [
        RoundContest(
            round=round,
            contest=contest,
            sample_size=sample_sizes.get(contest.id, None),
        )
        for contest in contests_that_havent_met_risk_limit
    ]

    # Create a new task to draw the sample in the background.
    round.draw_sample_task = create_background_task(
        draw_sample, dict(election_id=election.id, round_id=round.id),
    )

    record_activity(
        StartRound(
            timestamp=round.created_at,
            base=activity_base(election),
            round_num=round.round_num,
        )
    )

    db_session.commit()

    return jsonify({"status": "ok"})


def serialize_round(round: Round) -> dict:
    return {
        "id": round.id,
        "roundNum": round.round_num,
        "startedAt": isoformat(round.created_at),
        "endedAt": isoformat(round.ended_at),
        "isAuditComplete": is_audit_complete(round),
        "sampledAllBallots": sampled_all_ballots(round, round.election),
        "drawSampleTask": serialize_background_task(round.draw_sample_task),
    }


@api.route("/election/<election_id>/round", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def list_rounds_audit_admin(election: Election):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})


# Make a separate endpoint for jurisdiction admins to access the list of
# rounds. This makes our permission scheme simpler (every route only allows one
# user type), even though the logic of this particular pair our routes is
# identical.
@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def list_rounds_jurisdiction_admin(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify({"rounds": [serialize_round(r) for r in election.rounds]})
