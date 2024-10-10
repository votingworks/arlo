from datetime import datetime, timedelta
from typing import Dict, cast as typing_cast
from collections import Counter, defaultdict
from flask import jsonify
from werkzeug.exceptions import BadRequest


from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..database import db_session
from .shared import BatchTallies
from ..auth import restrict_access, UserType
from ..audit_math import (
    ballot_polling,
    macro,
    supersimple,
    sampler_contest,
    suite,
)
from ..audit_math.ballot_polling import SampleSizeOption
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
from ..util.string import format_count


def validate_all_manifests_uploaded(contest: Contest):
    if not all_manifests_uploaded(contest):
        raise UserError("Some jurisdictions haven't uploaded their manifests yet")


def validate_batch_tallies(contest):
    total_votes_by_choice: Dict[str, int] = defaultdict(int)
    for jurisdiction in contest.jurisdictions:
        batch_tallies = typing_cast(BatchTallies, jurisdiction.batch_tallies)
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
                f" ({format_count(total_votes_by_choice[choice.id], 'vote', 'votes')})"
                " is greater than the reported number of votes for that choice"
                f" ({format_count(choice.num_votes, 'vote', 'votes')})."
            )


def validate_hybrid_manifests_and_cvrs(contest: Contest):
    total_manifest_ballots = sum(
        jurisdiction.manifest_num_ballots or 0 for jurisdiction in contest.jurisdictions
    )
    total_votes = sum(choice.num_votes for choice in contest.choices)
    assert contest.votes_allowed is not None
    if total_votes > total_manifest_ballots * contest.votes_allowed:
        raise UserError(
            f"Contest {contest.name} vote counts add up to {format_count(total_votes, 'vote', 'votes')},"
            f" which is more than the total number of ballots across all"
            f" jurisdiction manifests ({format_count(total_manifest_ballots, 'ballot', 'ballots')})"
            f" times the number of votes allowed ({format_count(contest.votes_allowed, 'vote', 'votes')})"
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
            f"For contest {contest.name}, found {format_count(cvr_ballots, 'ballot', 'ballots')} in the CVRs,"
            f" which is more than the total number of CVR ballots across all jurisdiction manifests ({manifest_ballots.cvr})"
            " for jurisdictions in this contest's universe"
        )

    vote_counts = hybrid_contest_choice_vote_counts(contest)
    assert vote_counts is not None
    non_cvr_votes = sum(count.non_cvr for count in vote_counts.values())
    if manifest_ballots.non_cvr * contest.votes_allowed < non_cvr_votes:
        raise UserError(
            f"For contest {contest.name}, choice votes for non-CVR ballots add up to"
            f" {format_count(non_cvr_votes, 'vote', 'votes')},"
            f" which is more than the total number of non-CVR ballots across all jurisdiction manifests"
            f" ({format_count(manifest_ballots.non_cvr, 'ballot', 'ballots')})"
            " for jurisdictions in this contest's universe times the number of votes allowed"
            f" ({format_count(contest.votes_allowed, 'vote', 'votes')})"
        )

    choices_by_id = {choice.id: choice for choice in contest.choices}
    invalid_count = next(
        (
            (choices_by_id[choice_id], count)
            for choice_id, count in vote_counts.items()
            if count.cvr > choices_by_id[choice_id].num_votes
        ),
        None,
    )
    if invalid_count:
        choice, count = invalid_count
        raise UserError(
            f"For contest {contest.name}, the CVRs contain more votes for choice {choice.name}"
            f" ({format_count(count.cvr, 'vote', 'votes')})"
            f" than were entered in the contest settings"
            f" ({format_count(choice.num_votes, 'vote', 'votes')})."
        )


def sample_size_options(election: Election) -> Dict[str, Dict[str, SampleSizeOption]]:
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
                rounds.batch_tallies(contest),
                rounds.sampled_batch_results(contest),
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

    try:
        return {
            contest.id: sample_sizes_for_contest(contest)
            for contest in rounds.active_targeted_contests(election)
        }
    except ValueError as exc:
        raise UserError(exc) from exc  # pragma: no cover


@background_task
def next_round_sample_size_options(election_id: str):
    election = Election.query.get(election_id)
    current_round = rounds.get_current_round(election)
    next_round_num = current_round.round_num + 1 if current_round else 1
    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election.id, round_num=next_round_num
    ).one()
    sample_sizes.sample_size_options = sample_size_options(election)


# In rounds other than the first round, we want to automatically select a sample
# size from the generated options instead of letting the user pick.
def autoselect_sample_size(options: Dict[str, SampleSizeOption], audit_type: AuditType):
    if audit_type == AuditType.BALLOT_POLLING:
        return options.get("0.9", options.get("asn"))
    elif audit_type == AuditType.BATCH_COMPARISON:
        return options["macro"]
    elif audit_type == AuditType.BALLOT_COMPARISON:
        return options["supersimple"]
    else:
        assert audit_type == AuditType.HYBRID
        return options["suite"]


def serialize_sample_size_options(sample_size_options):
    if sample_size_options is None:
        return None
    return {
        contest_id: list(options.values())
        for contest_id, options in sample_size_options.items()
    }


@api.route("/election/<election_id>/sample-sizes/<int:round_num>", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_sample_sizes(election: Election, round_num: int):
    current_round = rounds.get_current_round(election)
    next_round_num = current_round.round_num + 1 if current_round else 1
    if not 1 <= round_num <= next_round_num:
        raise BadRequest("Invalid round number")

    sample_sizes = SampleSizeOptions.query.filter_by(
        election_id=election.id,
        round_num=round_num,
    ).one_or_none()
    # If we've never queried sample sizes before for this round, create a row in
    # the database to store them.
    if not sample_sizes:
        sample_sizes = SampleSizeOptions(election_id=election.id, round_num=round_num)
        db_session.add(sample_sizes)

    # If we don't have sample sizes stored already, or we do but they expired,
    # start a background task to compute sample size options. We invalidate
    # sample size options after 5 seconds because they depend on a lot of data
    # that might change (e.g. manifests, CVRs, contest settings, random seed),
    # so we want to recompute them whenever they are requested.
    existing_options_expired = (
        sample_sizes.task
        and sample_sizes.task.completed_at
        and (
            datetime.now(timezone.utc) - sample_sizes.task.completed_at
            > timedelta(seconds=5)
        )
    )
    if round_num == next_round_num and (
        not sample_sizes.task or existing_options_expired
    ):
        sample_sizes.sample_size_options = None
        sample_sizes.task = create_background_task(
            next_round_sample_size_options, dict(election_id=election.id)
        )

        db_session.flush()  # Ensure we can read task.created_at
        activity_log.record_activity(
            activity_log.CalculateSampleSizes(
                timestamp=sample_sizes.task.created_at,
                base=activity_log.activity_base(election),
            )
        )

        db_session.commit()

    # If the round already started, return which sample size was selected for
    # each contest so we can show the user
    selected_sample_sizes = (
        dict(
            RoundContest.query.join(Round)
            .filter_by(election_id=election.id, round_num=round_num)
            .values(RoundContest.contest_id, RoundContest.sample_size)
        )
        if current_round and round_num < next_round_num
        else None
    )

    options = sample_sizes.sample_size_options and (
        sample_sizes.sample_size_options
        if round_num == 1
        else {
            contest_id: {
                "_": autoselect_sample_size(options, AuditType(election.audit_type))
            }
            for contest_id, options in sample_sizes.sample_size_options.items()
        }
    )

    return jsonify(
        sampleSizes=serialize_sample_size_options(options),
        selected=selected_sample_sizes,
        task=serialize_background_task(sample_sizes.task),
    )
