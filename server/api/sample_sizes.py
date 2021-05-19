from datetime import datetime, timedelta
from typing import Dict
from collections import Counter, defaultdict
from flask import jsonify

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from ..auth import restrict_access, UserType
from ..audit_math import (
    ballot_polling,
    macro,
    supersimple,
    sampler_contest,
    suite,
)
from . import rounds  # pylint: disable=cyclic-import
from .cvrs import validate_uploaded_cvrs, hybrid_contest_choice_vote_counts
from .ballot_manifest import hybrid_contest_total_ballots, all_manifests_uploaded
from ..worker.tasks import (
    serialize_background_task,
    create_background_task,
    background_task,
    UserError,
)
from .. import activity_log


def validate_all_manifests_uploaded(contest: Contest):
    if not all_manifests_uploaded(contest):
        raise UserError("Some jurisdictions haven't uploaded their manifests yet")


def validate_batch_tallies(contest):
    total_votes_by_choice: Dict[str, int] = defaultdict(int)
    for jurisdiction in contest.jurisdictions:
        batch_tallies = typing_cast(rounds.BatchTallies, jurisdiction.batch_tallies)
        if batch_tallies is None:
            raise UserError(
                "Some jurisdictions haven't uploaded their batch tallies files yet."
            )
        for tally in batch_tallies.values():
            for choice_id, votes in tally[contest.id].items():
                total_votes_by_choice[choice_id] += votes

    for choice in contest.choices:
        if total_votes_by_choice[choice.id] > choice.num_votes:
            raise UserError(
                f"Total votes in batch tallies files for contest choice {choice.name}"
                f" ({total_votes_by_choice[choice.id]}) is greater than the"
                f" reported number of votes for that choice ({choice.num_votes})."
            )


def validate_hybrid_manifests_and_cvrs(contest: Contest):
    total_manifest_ballots = sum(
        jurisdiction.manifest_num_ballots or 0 for jurisdiction in contest.jurisdictions
    )
    total_votes = sum(choice.num_votes for choice in contest.choices)
    assert contest.votes_allowed is not None
    if total_votes > total_manifest_ballots * contest.votes_allowed:
        raise UserError(
            f"Contest {contest.name} vote counts add up to {total_votes},"
            f" which is more than the total number of ballots across all jurisdiction manifests ({total_manifest_ballots})"
            f" times the number of votes allowed ({contest.votes_allowed})"
        )

    manifest_ballots = hybrid_contest_total_ballots(contest)
    cvr_ballots = (
        CvrBallot.query.join(Batch)
        .join(Jurisdiction)
        .join(Jurisdiction.contests)
        .filter_by(id=contest.id)
        .count()
    )
    if manifest_ballots.cvr < cvr_ballots:
        raise UserError(
            f"For contest {contest.name}, found {cvr_ballots} ballots in the CVRs,"
            f" which is more than the total number of CVR ballots across all jurisdiction manifests ({manifest_ballots.cvr})"
            " for jurisdictions in this contest's universe"
        )

    vote_counts = hybrid_contest_choice_vote_counts(contest)
    assert vote_counts is not None
    non_cvr_votes = sum(count.non_cvr for count in vote_counts.values())
    if manifest_ballots.non_cvr * contest.votes_allowed < non_cvr_votes:
        raise UserError(
            f"For contest {contest.name}, choice votes for non-CVR ballots add up to {non_cvr_votes},"
            f" which is more than the total number of non-CVR ballots across all jurisdiction manifests ({manifest_ballots.non_cvr})"
            " for jurisdictions in this contest's universe"
            f" times the number of votes allowed ({contest.votes_allowed})"
        )


def sample_size_options(
    election: Election,
) -> Dict[str, Dict[str, ballot_polling.SampleSizeOption]]:
    if not election.contests:
        raise UserError("Cannot compute sample sizes until contests are set")
    if election.risk_limit is None:
        raise UserError("Cannot compute sample sizes until risk limit is set")

    def sample_sizes_for_contest(contest: Contest):
        assert election.risk_limit is not None
        if election.audit_type == AuditType.BALLOT_POLLING:
            sample_results = rounds.contest_results_by_round(contest)
            sample_size_options = ballot_polling.get_sample_size(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                sample_results,
                AuditMathType(election.audit_math_type),
                rounds.round_sizes(contest),
            )
            # Remove unnecessary "type" field from options, add "key" field
            return {
                key: {"key": key, "size": option["size"], "prob": option["prob"]}
                for key, option in sample_size_options.items()
            }

        elif election.audit_type == AuditType.BATCH_COMPARISON:
            validate_batch_tallies(contest)

            sample_size = macro.get_sample_sizes(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                rounds.batch_tallies(election),
                rounds.sampled_batch_results(election),
            )
            return {"macro": {"key": "macro", "size": sample_size, "prob": None}}

        elif election.audit_type == AuditType.BALLOT_COMPARISON:
            validate_all_manifests_uploaded(contest)
            validate_uploaded_cvrs(contest)

            contest_for_sampler = sampler_contest.from_db_contest(contest)

            num_previous_samples = SampledBallotDraw.query.filter_by(
                contest_id=contest.id
            ).count()
            discrepancies = supersimple.compute_discrepancies(
                contest_for_sampler,
                rounds.cvrs_for_contest(contest),
                rounds.sampled_ballot_interpretations_to_cvrs(contest),
            )
            discrepancy_counter = Counter(
                d["counted_as"] for d in discrepancies.values()
            )
            discrepancy_counts = {
                "sample_size": num_previous_samples,
                "1-under": discrepancy_counter[-1],
                "1-over": discrepancy_counter[1],
                "2-under": discrepancy_counter[-2],
                "2-over": discrepancy_counter[2],
            }

            sample_size = supersimple.get_sample_sizes(
                election.risk_limit, contest_for_sampler, discrepancy_counts
            )
            return {
                "supersimple": {"key": "supersimple", "size": sample_size, "prob": None}
            }

        else:
            assert election.audit_type == AuditType.HYBRID

            validate_all_manifests_uploaded(contest)
            validate_uploaded_cvrs(contest)
            validate_hybrid_manifests_and_cvrs(contest)

            non_cvr_stratum, cvr_stratum = rounds.hybrid_contest_strata(contest)
            size = suite.get_sample_size(
                election.risk_limit,
                sampler_contest.from_db_contest(contest),
                non_cvr_stratum,
                cvr_stratum,
            )

            return {
                "suite": {
                    "key": "suite",
                    "sizeCvr": size.cvr,
                    "sizeNonCvr": size.non_cvr,
                    "size": size.cvr + size.non_cvr,
                    "prob": None,
                }
            }

    targeted_contests = Contest.query.filter_by(
        election_id=election.id, is_targeted=True
    )
    targeted_contests_that_havent_met_risk_limit = (
        targeted_contests.all()
        if len(list(election.rounds)) == 0
        else targeted_contests.join(RoundContest).filter_by(is_complete=False).all()
    )
    try:
        return {
            contest.id: sample_sizes_for_contest(contest)
            for contest in targeted_contests_that_havent_met_risk_limit
        }
    except ValueError as exc:
        raise UserError(exc) from exc


@background_task
def first_round_sample_size_options(election_id: str):
    election = Election.query.get(election_id)
    election.sample_size_options = sample_size_options(election)


def serialize_sample_size_options(sample_size_options):
    if sample_size_options is None:
        return None
    return {
        contest_id: list(options.values())
        for contest_id, options in sample_size_options.items()
    }


@api.route("/election/<election_id>/sample-sizes", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_sample_sizes(election: Election):
    # If we don't have sample sizes stored already, or we do but they expired,
    # start a background task to compute sample size options. We invalidate
    # sample size options after 5 seconds because they depend on a lot of data
    # that might change (e.g. manifests, CVRs, contest settings, random seed),
    # so we want to recompute them whenever they are requested.
    existing_options_expired = (
        election.sample_size_options_task
        and election.sample_size_options_task.completed_at
        and (
            datetime.now(timezone.utc) - election.sample_size_options_task.completed_at
            > timedelta(seconds=5)
        )
        # Don't need to recompute after the audit launches
        and len(list(election.rounds)) == 0
    )
    if not election.sample_size_options_task or existing_options_expired:
        election.sample_size_options = None
        election.sample_size_options_task = create_background_task(
            first_round_sample_size_options, dict(election_id=election.id)
        )

        db_session.flush()  # Ensure we can read task.created_at
        activity_log.record_activity(
            activity_log.CalculateSampleSizes(
                timestamp=election.sample_size_options_task.created_at,
                base=activity_log.activity_base(election),
            )
        )

        db_session.commit()

    # If we've already started the first round, return which sample size was
    # selected for each contest so we can show the user
    selected_sample_sizes = (
        dict(
            RoundContest.query.join(Round)
            .filter_by(election_id=election.id, round_num=1)
            .values(RoundContest.contest_id, RoundContest.sample_size)
        )
        if len(list(election.rounds)) > 0
        else None
    )

    return jsonify(
        sampleSizes=serialize_sample_size_options(election.sample_size_options),
        selected=selected_sample_sizes,
        task=serialize_background_task(election.sample_size_options_task),
    )
