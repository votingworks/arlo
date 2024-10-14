from collections import defaultdict
import random
from typing import Dict, List, Optional, Tuple, TypedDict, Union
from sqlalchemy import and_, func, literal, true
from sqlalchemy.orm import joinedload, load_only


from ..models import *  # pylint: disable=wildcard-import
from ..audit_math import (
    ballot_polling_types,
    macro,
    sampler,
    sampler_contest,
    suite,
    supersimple,
)
from ..util.collections import group_by
from .ballot_manifest import hybrid_contest_total_ballots
from .cvrs import cvr_contests_metadata, hybrid_contest_choice_vote_counts
from ..feature_flags import is_enabled_sample_extra_batches_by_counting_group


def get_current_round(election: Election) -> Optional[Round]:
    if len(list(election.rounds)) == 0:
        return None
    return max(election.rounds, key=lambda r: r.round_num)


def get_previous_round(election: Election, round: Round) -> Optional[Round]:
    if round.round_num == 1:
        return None
    return next(r for r in election.rounds if r.round_num == round.round_num - 1)


def contest_results_by_round(
    contest: Contest,
) -> Optional[ballot_polling_types.BALLOT_POLLING_SAMPLE_RESULTS]:
    results_by_round: ballot_polling_types.BALLOT_POLLING_SAMPLE_RESULTS = defaultdict(
        lambda: defaultdict(int)
    )
    for result in contest.results:
        results_by_round[result.round_id][result.contest_choice_id] = result.result
    return results_by_round if len(results_by_round) > 0 else None


# Returns a list of targeted contests that are still being audited (i.e. haven't
# yet met the risk limit)
def active_targeted_contests(election: Election) -> List[Contest]:
    targeted_contests = Contest.query.filter_by(
        election_id=election.id, is_targeted=True
    )
    return list(
        targeted_contests.all()
        if len(list(election.rounds)) == 0
        else targeted_contests.join(RoundContest).filter_by(is_complete=False).all()
    )


def samples_not_found_by_round(contest: Contest) -> Dict[str, int]:
    if contest.is_targeted:
        return dict(
            SampledBallotDraw.query.filter_by(contest_id=contest.id)
            .join(SampledBallot)
            .filter_by(status=BallotStatus.NOT_FOUND)
            .group_by(SampledBallotDraw.round_id)
            .values(SampledBallotDraw.round_id, func.count())
        )
    else:
        return dict(
            SampledBallot.query.filter_by(status=BallotStatus.NOT_FOUND)
            .join(Batch)
            .join(Jurisdiction)
            .join(Jurisdiction.contests)
            .filter_by(id=contest.id)
            .join(SampledBallot.draws)
            .group_by(SampledBallotDraw.round_id)
            .values(SampledBallotDraw.round_id, func.count(SampledBallot.id.distinct()))
        )


# { batch_key: { contest_id: { choice_id: votes }}}
BatchTallies = Dict[macro.BatchKey, macro.BatchResults]


def batch_tallies(contest: Contest) -> BatchTallies:
    # Key each batch by jurisdiction name and batch name since batch names
    # are only guaranteed unique within a jurisdiction
    return {
        (jurisdiction.name, batch_name): tally
        for jurisdiction in contest.jurisdictions
        for batch_name, tally in jurisdiction.batch_tallies.items()  # type: ignore
    }


def sampled_batch_results(
    contest: Contest, include_non_rla_batches=False
) -> BatchTallies:
    results_by_batch_and_choice = (
        Batch.query.filter(
            Batch.id.in_(
                Batch.query.join(Jurisdiction)
                .filter(Jurisdiction.election_id == contest.election_id)
                .join(SampledBatchDraw)
                # Don't include non-RLA batches unless explicitly requested, e.g., for discrepancy
                # and audit reports
                .filter(
                    (
                        true()
                        if include_non_rla_batches
                        else and_(
                            SampledBatchDraw.contest_id == contest.id,
                            SampledBatchDraw.ticket_number != EXTRA_TICKET_NUMBER,
                        )
                    ),
                )
                .values(Batch.id)
            )
        )
        .join(Jurisdiction)
        .join(Jurisdiction.contests)
        .filter(Contest.id == contest.id)
        .join(ContestChoice)
        .outerjoin(BatchResultTallySheet)
        .outerjoin(
            BatchResult,
            and_(
                BatchResult.tally_sheet_id == BatchResultTallySheet.id,
                BatchResult.contest_choice_id == ContestChoice.id,
            ),
        )
        .group_by(Jurisdiction.name, Batch.name, ContestChoice.id)
        .values(
            Jurisdiction.name,
            Batch.name,
            ContestChoice.id,
            func.sum(func.coalesce(BatchResult.result, 0)),
        )
    )
    results_by_batch = group_by(
        results_by_batch_and_choice,
        key=lambda result: (result[0], result[1]),  # (jurisdiction_name, batch_name)
    )
    return {
        batch_key: {
            contest.id: {
                choice_id: result for (_, _, choice_id, result) in batch_results
            }
        }
        for batch_key, batch_results in results_by_batch.items()
    }


def sampled_batches_by_ticket_number(contest: Contest) -> Dict[str, sampler.BatchKey]:
    batches_by_ticket_number = (
        SampledBatchDraw.query.join(Batch)
        .join(Jurisdiction)
        .filter(Jurisdiction.election_id == contest.election_id)
        # Don't include non-RLA batches
        .filter(
            and_(
                SampledBatchDraw.contest_id == contest.id,
                SampledBatchDraw.ticket_number != EXTRA_TICKET_NUMBER,
            )
        )
        .order_by(SampledBatchDraw.ticket_number)
        .values(SampledBatchDraw.ticket_number, Jurisdiction.name, Batch.name)
    )
    return {
        ticket_number: (jurisdiction_name, batch_name)
        for ticket_number, jurisdiction_name, batch_name in batches_by_ticket_number
    }


def round_sizes(contest: Contest) -> ballot_polling_types.BALLOT_POLLING_ROUND_SIZES:
    # For targeted contests, return the number of ballots sampled for that contest
    if contest.is_targeted:
        results = (
            Round.query.join(SampledBallotDraw)
            .filter_by(contest_id=contest.id)
            .group_by(Round.id, Round.round_num)
            .values(
                Round.round_num, Round.id, func.count(SampledBallotDraw.ticket_number)
            )
        )
        return {
            round_num: ballot_polling_types.RoundInfo(round_id, count)
            for round_num, round_id, count in results
        }
    # For opportunistic contests, return the number of sampled ballots in
    # jurisdictions in that contest's universe
    else:
        contest_jurisdiction_ballots = (
            SampledBallot.query.join(Batch)
            .join(Jurisdiction)
            .join(Jurisdiction.contests)
            .filter_by(id=contest.id)
            .with_entities(SampledBallot.id)
            .subquery()
        )
        results = (
            Round.query.join(SampledBallotDraw)
            .join(SampledBallot)
            .filter(SampledBallot.id.in_(contest_jurisdiction_ballots))
            .group_by(Round.id, Round.round_num)
            .values(Round.round_num, Round.id, func.count(SampledBallot.id.distinct()))
        )
        return {
            round_num: ballot_polling_types.RoundInfo(round_id, count)
            for round_num, round_id, count in results
        }


def cvrs_for_contest(contest: Contest) -> sampler_contest.CVRS:
    cvrs: sampler_contest.CVRS = {}

    ballot_interpretations = (
        CvrBallot.query.join(Batch)
        .join(Jurisdiction)
        .join(Jurisdiction.contests)
        .filter_by(id=contest.id)
        .join(
            SampledBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .values(Jurisdiction.id, SampledBallot.id, CvrBallot.interpretations)
    )

    metadata_by_jurisdictions = {
        jurisdiction.id: cvr_contests_metadata(jurisdiction)
        for jurisdiction in contest.jurisdictions
    }

    for jurisdiction_id, ballot_key, interpretations_str in ballot_interpretations:
        metadata = metadata_by_jurisdictions[jurisdiction_id]
        assert metadata is not None
        choices_metadata = metadata[contest.name]["choices"]

        # interpretations is the raw CVR string: 1,0,0,1,0,1,0. We need to
        # pick out the interpretation for each contest choice. We saved the
        # column index for each choice when we parsed the CVR.
        interpretations = interpretations_str.split(",")
        choice_interpretations = {
            choice_name: interpretations[choice_metadata["column"]]
            for choice_name, choice_metadata in choices_metadata.items()
        }

        # If the interpretations are empty, it means the contest wasn't
        # on the ballot, so we should skip this contest entirely for
        # this ballot.
        if all(
            interpretation == "" for interpretation in choice_interpretations.values()
        ):
            cvrs[ballot_key] = {}
        else:
            # Parse each choice's interpretation. We use the main list of
            # contest choices since each jurisdiction's CVR may only record
            # a subset of the choices (e.g. in ES&S/Hart). If there's a
            # choice we don't have a CVR interpretation for, we can assume
            # it didn't get voted for and set its interpretation to 0.
            cvrs[ballot_key] = {
                contest.id: {
                    choice.id: choice_interpretations.get(choice.name, "0")
                    for choice in contest.choices
                }
            }

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
        load_only(SampledBallot.id, SampledBallot.status),
        joinedload(SampledBallot.interpretations)
        .load_only(BallotInterpretation.contest_id, BallotInterpretation.interpretation)
        .joinedload(BallotInterpretation.selected_choices)
        .load_only(ContestChoice.id),
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
            if (
                interpretation is None  # Legacy case for contest not on ballot
                or interpretation.interpretation == Interpretation.CONTEST_NOT_ON_BALLOT
            ):
                ballot_cvr = {}
            elif interpretation.interpretation == Interpretation.BLANK:
                ballot_cvr = {
                    contest.id: {choice.id: "0" for choice in contest.choices}
                }
            elif interpretation.interpretation == Interpretation.VOTE:
                ballot_cvr = {
                    contest.id: {
                        choice.id: (
                            "1"
                            if any(
                                selected_choice.id == choice.id
                                for selected_choice in interpretation.selected_choices
                            )
                            else "0"
                        )
                        for choice in contest.choices
                    }
                }
            else:
                raise Exception(
                    f"Unexpected interpretation type: {interpretation.interpretation}"
                )  # pragma: no cover

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
        suite_contest,
        cvr_reported_results,
        cvr_sample_results,
    )
    # Create a stratum for CVR ballots
    cvr_stratum = suite.BallotComparisonStratum(
        total_ballots.cvr,
        cvr_vote_counts,
        cvr_misstatements,
        cvr_previous_samples,
    )

    return non_cvr_stratum, cvr_stratum


# { choice_id: vote delta }
ContestVoteDeltas = Dict[str, int]


def ballot_vote_deltas(
    contest: Contest,
    reported_cvr: Optional[supersimple.CVR],
    audited_cvr: Optional[supersimple.CVR],
) -> Optional[Union[str, ContestVoteDeltas]]:
    if audited_cvr is None:
        return "Ballot not found"
    if reported_cvr is None:
        return "Ballot not in CVR"

    reported = reported_cvr.get(contest.id)
    audited = audited_cvr.get(contest.id)

    if audited is None and reported is None:
        return None
    if audited is None:
        audited = {choice.id: "0" for choice in contest.choices}
    if reported is None:
        reported = {choice.id: "0" for choice in contest.choices}

    deltas = {}
    for choice in contest.choices:
        reported_vote = (
            0 if reported[choice.id] in ["o", "u"] else int(reported[choice.id])
        )
        audited_vote = (
            0 if audited[choice.id] in ["o", "u"] else int(audited[choice.id])
        )
        deltas[choice.id] = reported_vote - audited_vote

    if all(delta == 0 for delta in deltas.values()):
        return None

    return deltas


def batch_vote_deltas(
    reported_results: macro.ChoiceVotes, audited_results: macro.ChoiceVotes
) -> Optional[ContestVoteDeltas]:
    deltas = {
        choice_id: reported_results[choice_id] - audited_results[choice_id]
        for choice_id in reported_results.keys()
        if choice_id != "ballots"
    }

    if all(delta == 0 for delta in deltas.values()):
        return None

    return deltas


# Calculates the sample size threshold to trigger a full hand tally in each
# targeted contest
def full_hand_tally_sizes(election: Election):
    contests_query = Contest.query.filter_by(election_id=election.id, is_targeted=True)
    if election.audit_type == AuditType.BATCH_COMPARISON:
        return dict(
            contests_query.join(Contest.jurisdictions)
            .group_by(Contest.id)
            .values(
                Contest.id,
                func.coalesce(func.sum(Jurisdiction.manifest_num_batches), 0),
            )
        )
    return dict(contests_query.values(Contest.id, Contest.total_ballots_cast))


# Returns True if the cumulative sample size up to the specified round for any targeted contest
# indicates that a full hand tally is needed
def needs_full_hand_tally(round: Round, election: Election) -> bool:
    full_hand_tally_size = full_hand_tally_sizes(election)
    cumulative_sample_sizes = dict(
        RoundContest.query.join(Round)
        .filter_by(election_id=round.election_id)
        .filter(Round.round_num <= round.round_num)
        .join(RoundContest.contest)
        .filter_by(is_targeted=True)
        .group_by(RoundContest.contest_id)
        .values(
            RoundContest.contest_id,
            func.sum(RoundContest.sample_size["size"].as_integer()),
        )
    )
    return any(
        size >= full_hand_tally_size[contest_id]
        for contest_id, size in cumulative_sample_sizes.items()
    )


# Returns True if Arlo is in full hand tally mode, which is only triggered
# in the first round of ballot polling audits when the sample size requires a
# full hand tally
def is_full_hand_tally(round: Round, election: Election):
    return (
        election.audit_type == AuditType.BALLOT_POLLING
        and round.round_num == 1
        and needs_full_hand_tally(round, election)
    )


class SampleSize(TypedDict):
    size: int
    key: str
    prob: Optional[float]
    sizeCvr: int  # Only in hybrid audits
    sizeNonCvr: int  # Only in hybrid audits


class BallotDraw(TypedDict):
    batch_id: str
    ballot_position: int
    contest_id: str
    ticket_number: str


class BatchDraw(TypedDict):
    batch_id: str
    contest_id: str
    ticket_number: str


def compute_sample_batches_for_contest(
    election: Election,
    round_num: int,
    contest: Contest,
    contest_sample_size: SampleSize,
) -> List[BatchDraw]:
    # Create a mapping from batch keys used in the sampling back to batch ids
    batches = (
        Batch.query.join(Jurisdiction)
        .filter(Jurisdiction.election_id == contest.election_id)
        .with_entities(Jurisdiction.name, Batch.name, Batch.id)
    )
    batch_key_to_id = {
        (jurisdiction_name, batch_name): batch_id
        for jurisdiction_name, batch_name, batch_id in batches
    }

    previously_sampled_batch_keys: List[sampler.BatchKey] = list(
        Batch.query.join(Jurisdiction)
        .filter(Jurisdiction.election_id == contest.election_id)
        .join(SampledBatchDraw)
        # Don't include non-RLA batches
        .filter(
            and_(
                SampledBatchDraw.contest_id == contest.id,
                SampledBatchDraw.ticket_number != EXTRA_TICKET_NUMBER,
            )
        )
        .with_entities(Jurisdiction.name, Batch.name)
    )

    sample = sampler.draw_ppeb_sample(
        str(election.random_seed),
        sampler_contest.from_db_contest(contest),
        contest_sample_size["size"],
        previously_sampled_batch_keys,
        batch_tallies(contest),
    )

    sample_batches = [
        BatchDraw(
            batch_id=batch_key_to_id[batch_key],
            contest_id=contest.id,
            ticket_number=ticket_number,
        )
        for ticket_number, batch_key in sample
    ]

    # Experimental feature
    # Add extra batches on top of the original sample that will be audited, but
    # not counted in the final risk measurement.
    if is_enabled_sample_extra_batches_by_counting_group(election) and round_num == 1:
        rand = random.Random(str(election.random_seed))
        for jurisdiction in contest.jurisdictions:
            batch_ids_with_container_and_num_ballots = (
                Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
                .with_entities(Batch.id, Batch.container, Batch.num_ballots)
                .all()
            )
            batch_ids = [
                batch_id for batch_id, _, _ in batch_ids_with_container_and_num_ballots
            ]
            batch_id_to_num_ballots = {
                batch_id: num_ballots
                for batch_id, _, num_ballots in batch_ids_with_container_and_num_ballots
            }
            # To simplify this experiment, we specify the counting group in the
            # container column of the ballot manifest
            bmd_batch_ids = {
                batch_id
                for batch_id, container, _ in batch_ids_with_container_and_num_ballots
                if container
                in [
                    "Advanced Voting",
                    "Advance Voting",
                    "Election Day",
                    "Elections Day",
                ]
            }
            hmpb_batch_ids = {
                batch_id
                for batch_id, container, _ in batch_ids_with_container_and_num_ballots
                if container in ["Absentee by Mail", "Provisional"]
            }
            sampled_batch_ids = {
                batch_key_to_id[batch_key]
                for _, batch_key in sample
                if batch_key[0] == jurisdiction.name
            }
            extra_batch_ids = set()
            # If we didn't sample any BMD batches, add one to the sample
            if len(bmd_batch_ids & sampled_batch_ids) == 0 and len(bmd_batch_ids) > 0:
                extra_bmd_batch_id = rand.choice(list(bmd_batch_ids))
                extra_batch_ids.add(extra_bmd_batch_id)
                sample_batches.append(
                    BatchDraw(
                        batch_id=extra_bmd_batch_id,
                        contest_id=contest.id,
                        ticket_number=EXTRA_TICKET_NUMBER,
                    )
                )
            # If we didn't sample any HMPB batches, add one to the sample
            if len(hmpb_batch_ids & sampled_batch_ids) == 0 and len(hmpb_batch_ids) > 0:
                extra_hmpb_batch_id = rand.choice(list(hmpb_batch_ids))
                extra_batch_ids.add(extra_hmpb_batch_id)
                sample_batches.append(
                    BatchDraw(
                        batch_id=extra_hmpb_batch_id,
                        contest_id=contest.id,
                        ticket_number=EXTRA_TICKET_NUMBER,
                    )
                )

            # Continue adding batches until the percentage of jurisdiction ballots selected is at
            # least 2%
            min_percentage_of_jurisdiction_ballots_selected = 0.02

            def compute_percentage_of_jurisdiction_ballots_selected(
                selected_batch_ids, num_jurisdiction_ballots
            ):
                num_jurisdiction_ballots_selected = sum(
                    # pylint: disable=cell-var-from-loop
                    batch_id_to_num_ballots[batch_id]
                    for batch_id in selected_batch_ids
                )
                return num_jurisdiction_ballots_selected / num_jurisdiction_ballots

            while (
                compute_percentage_of_jurisdiction_ballots_selected(
                    sampled_batch_ids.union(extra_batch_ids),
                    jurisdiction.manifest_num_ballots,
                )
                < min_percentage_of_jurisdiction_ballots_selected
            ):
                remaining_batch_ids = (
                    set(batch_ids) - sampled_batch_ids - extra_batch_ids
                )
                extra_batch_id = rand.choice(list(remaining_batch_ids))
                extra_batch_ids.add(extra_batch_id)
                sample_batches.append(
                    BatchDraw(
                        batch_id=extra_batch_id,
                        contest_id=contest.id,
                        ticket_number=EXTRA_TICKET_NUMBER,
                    )
                )

    return sample_batches


def compute_sample_batches(
    election: Election,
    round_num: int,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
) -> List[BatchDraw]:
    sample_batches = [
        batch
        for contest, sample_size in contest_sample_sizes
        for batch in compute_sample_batches_for_contest(
            election, round_num, contest, sample_size
        )
    ]
    return sample_batches


def compute_sample_ballots(
    election: Election,
    contest_sample_sizes: List[Tuple[Contest, SampleSize]],
    # For hybrid audits only, Batch.has_cvrs will be true/false if the batch
    # contains ballots with CVRs or not (based on the manifest).
    # filter_has_cvrs will constrain the ballots to sample based on
    # Batch.has_cvrs. Since Batch.has_cvrs is None for all other audit types,
    # the default filter is None.
    filter_has_cvrs: bool = None,
) -> List[BallotDraw]:
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

    def compute_sample_for_contest(
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
                batch_id=batch_key_to_id[batch_key],
                ballot_position=ballot_position,
                contest_id=contest.id,
                ticket_number=ticket_number,
            )
            for (ticket_number, (batch_key, ballot_position), _) in sample
        ]

    # Draw a sample for each contest
    samples = [
        sample
        for contest, sample_size in contest_sample_sizes
        for sample in compute_sample_for_contest(contest, sample_size)
    ]
    return samples
