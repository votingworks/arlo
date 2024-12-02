import io, csv
from typing import Dict, List, Optional, Tuple, Union, cast as typing_cast
from collections import defaultdict, Counter
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import aggregate_order_by
from werkzeug.exceptions import Conflict, BadRequest


from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..util.csv_download import (
    csv_response,
    election_timestamp_name,
    jurisdiction_timestamp_name,
)
from ..util.isoformat import isoformat
from ..util.collections import group_by
from ..audit_math import supersimple, sampler_contest, macro
from .ballot_manifest import hybrid_contest_total_ballots
from .cvrs import hybrid_contest_choice_vote_counts
from .batches import construct_batch_last_edited_by_string
from .shared import (
    ContestVoteDeltas,
    ballot_vote_deltas,
    batch_tallies,
    batch_vote_deltas,
    cvrs_for_contest,
    group_combined_batches,
    is_full_hand_tally,
    sampled_ballot_interpretations_to_cvrs,
    samples_not_found_by_round,
)
from .discrepancies import (
    show_ballot_comparison_discrepancies_by_jurisdiction,
    show_batch_comparison_discrepancies_by_jurisdiction,
)


def pretty_affiliation(affiliation: Optional[str]) -> str:
    mapping: Dict[str, str] = {
        Affiliation.DEMOCRAT: "Democrat",
        Affiliation.REPUBLICAN: "Republican",
        Affiliation.LIBERTARIAN: "Libertarian",
        Affiliation.INDEPENDENT: "Independent",
        Affiliation.OTHER: "Other",
    }
    return mapping.get(affiliation or "", "")


def pretty_boolean(boolean: bool) -> str:
    return "Yes" if boolean else "No"


def pretty_targeted(is_targeted: bool) -> str:
    return "Targeted" if is_targeted else "Opportunistic"


def pretty_pvalue(value: float) -> str:
    if value is None:
        return ""
    elif value == 0:
        return "0"
    elif value < 10**-10:
        return "<0.0000000001"
    else:
        ret = f"{round(value, 10):1.10f}".rstrip("0")
        # If we've stripped off the zero right after the decimal, put it back
        if ret[-1] == ".":
            ret += "0"
        return ret


# (round_num, contest_id, ticket_number)
TicketNumberTuple = Tuple[str, str, str]


def pretty_ballot_ticket_numbers(
    ticket_number_tuples: List[TicketNumberTuple],
    targeted_contests: List[Contest],
) -> List[str]:
    columns = []
    for contest in targeted_contests:
        contest_tuples = [
            ticket_number_tuple
            for ticket_number_tuple in ticket_number_tuples
            if ticket_number_tuple[1] == contest.id
        ]
        ticket_numbers = []
        for round_num, round_tuples in group_by(
            contest_tuples, key=lambda tuple: tuple[0]  # round_num
        ).items():
            ticket_numbers_str = ", ".join(
                sorted(ticket_number for _, _, ticket_number in round_tuples)
            )
            ticket_numbers.append(f"Round {round_num}: {ticket_numbers_str}")
        columns.append(", ".join(ticket_numbers))
    return columns


def pretty_batch_ticket_numbers_for_contest(
    batch: Batch, round_id_to_num: Dict[str, int], contest_id: str
) -> str:
    ticket_numbers = []
    for round_num, draws in group_by(
        list(batch.draws), key=lambda d: round_id_to_num[d.round_id]
    ).items():
        ticket_numbers_for_round = sorted(
            d.ticket_number for d in draws if d.contest_id == contest_id
        )
        if len(ticket_numbers_for_round) > 0:
            ticket_numbers_string = ", ".join(ticket_numbers_for_round)
            ticket_numbers.append(f"Round {round_num}: {ticket_numbers_string}")
    return ", ".join(ticket_numbers)


def pretty_batch_ticket_numbers(
    batch: Batch, round_id_to_num: Dict[str, int], contests: List[Contest]
) -> List[str]:
    return [
        pretty_batch_ticket_numbers_for_contest(batch, round_id_to_num, contest.id)
        for contest in contests
    ]


# (contest_id, interpretation, selected_choice_names, comment, is_overvote, has_invalid_write_in)
InterpretationTuple = Tuple[str, str, List[str], str, bool, bool]


def pretty_ballot_interpretation(
    interpretations: List[InterpretationTuple],
    contest: Contest,
) -> str:
    interpretation = next((i for i in interpretations if i[0] == contest.id), None)
    # Legacy case: we used to not require an interpretation for every contest
    # before we had Interpretation.CONTEST_NOT_ON_BALLOT
    if not interpretation:
        return ""

    (
        _contest_id,
        interpretation_str,
        selected_choice_names,
        comment,
        is_overvote,
        has_invalid_write_in,
    ) = interpretation

    choices = ""
    if interpretation_str == Interpretation.VOTE:
        choices = ", ".join(selected_choice_names)
        if has_invalid_write_in:
            choices += ", INVALID_WRITE_IN"
    elif interpretation_str == Interpretation.BLANK:
        choices = "INVALID_WRITE_IN" if has_invalid_write_in else interpretation_str
    else:
        choices = interpretation_str
    overvote = "OVERVOTE; " if is_overvote else ""
    comment = f"; COMMENT: {comment}" if comment else ""
    return overvote + choices + comment


def pretty_cvr_interpretation(
    ballot: SampledBallot, contest: Contest, contest_cvrs: supersimple.CVRS
) -> str:
    ballot_cvr = contest_cvrs.get(ballot.id)
    cvrs_by_choice = ballot_cvr and ballot_cvr.get(contest.id)
    # If CVR was missing/empty for this contest for this ballot, skip it
    if ballot_cvr is None or cvrs_by_choice is None:
        return ""

    if "o" in cvrs_by_choice.values():
        return "Overvote"
    if "u" in cvrs_by_choice.values():
        return "Undervote"

    if all(interpretation == "0" for interpretation in cvrs_by_choice.values()):
        return "Blank"

    choice_id_to_name = {choice.id: choice.name for choice in contest.choices}
    return ", ".join(
        choice_id_to_name[choice_id]
        for choice_id, interpretation in cvrs_by_choice.items()
        if interpretation == "1"
    )


def add_sign(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def pretty_vote_deltas(
    contest: Contest,
    vote_deltas: Optional[Union[str, ContestVoteDeltas]],
) -> str:
    if vote_deltas is None:
        return ""
    if isinstance(vote_deltas, str):
        return vote_deltas

    return pretty_choice_votes(
        {
            choice.name: add_sign(vote_deltas[choice.id])
            for choice in contest.choices
            if vote_deltas[choice.id] != 0
        }
    )


def pretty_discrepancy(
    ballot: SampledBallot,
    contest_discrepancies: Dict[str, supersimple.Discrepancy],
) -> str:
    if ballot.id in contest_discrepancies:
        return str(contest_discrepancies[ballot.id]["counted_as"])
    else:
        return ""


def pretty_choice_votes(
    choice_votes: Dict[str, Union[int, str]], not_found: Optional[int] = None
) -> str:
    return "; ".join(
        [f"{name}: {votes}" for name, votes in choice_votes.items()]
        + (
            [f"Ballots not found (counted for loser): {not_found}"]
            if not_found is not None
            else []
        )
    )


def heading(heading: str):
    return [f"######## {heading} ########"]


def election_info_rows(election: Election):
    return [
        heading("ELECTION INFO"),
        ["Organization", "Election Name", "State"],
        [election.organization.name, election.election_name, election.state],
    ]


def contest_rows(election: Election):
    rows = [
        heading("CONTESTS"),
        [
            "Contest Name",
            "Targeted?",
            "Number of Winners",
            "Votes Allowed",
            "Total Ballots Cast",
            "Vote Totals",
        ]
        + (
            ["Vote Totals from Batches", "Pending Ballots"]
            if election.audit_type == AuditType.BATCH_COMPARISON
            else []
        )
        + (
            [
                "Total Ballots Cast: CVR",
                "Total Ballots Cast: Non-CVR",
                "Vote Totals: CVR",
                "Vote Totals: Non-CVR",
            ]
            if election.audit_type == AuditType.HYBRID
            else []
        ),
    ]

    for contest in election.contests:
        row = [
            contest.name,
            pretty_targeted(contest.is_targeted),
            contest.num_winners,
            contest.votes_allowed,
            contest.total_ballots_cast,
            pretty_choice_votes(
                {choice.name: choice.num_votes for choice in contest.choices}
            ),
        ]

        if election.audit_type == AuditType.BATCH_COMPARISON:
            tallies = batch_tallies(contest)
            row.append(
                pretty_choice_votes(
                    {
                        choice.name: sum(
                            tally.get(contest.id, {}).get(choice.id, 0)
                            for tally in tallies.values()
                        )
                        for choice in contest.choices
                    }
                )
            )
            row.append(contest.pending_ballots or 0)

        if election.audit_type == AuditType.HYBRID:
            total_ballots = hybrid_contest_total_ballots(contest)
            vote_counts = hybrid_contest_choice_vote_counts(contest)
            if total_ballots and vote_counts:
                choice_id_to_name = {
                    choice.id: choice.name for choice in contest.choices
                }
                row = row + [
                    total_ballots.cvr,
                    total_ballots.non_cvr,
                    pretty_choice_votes(
                        {
                            choice_id_to_name[choice_id]: count.cvr
                            for choice_id, count in vote_counts.items()
                        }
                    ),
                    pretty_choice_votes(
                        {
                            choice_id_to_name[choice_id]: count.non_cvr
                            for choice_id, count in vote_counts.items()
                        }
                    ),
                ]
        rows.append(row)
    return rows


def contest_name_standardization_rows(election: Election):
    if election.audit_type not in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        return None

    standardization_rows = [
        [jurisdiction.name, contest_name, cvr_contest_name]
        for jurisdiction in election.jurisdictions
        if jurisdiction.contest_name_standardizations
        for contest_name, cvr_contest_name in typing_cast(
            Dict, jurisdiction.contest_name_standardizations
        ).items()
    ]
    if len(standardization_rows) == 0:
        return None

    return [
        heading("CONTEST NAME STANDARDIZATIONS"),
        ["Jurisdiction", "Contest Name", "CVR Contest Name"],
    ] + standardization_rows


def audit_settings_rows(election: Election):
    return [
        heading("AUDIT SETTINGS"),
        [
            "Audit Name",
            "Audit Type",
            "Audit Math Type",
            "Risk Limit",
            "Random Seed",
            "Online Data Entry?",
        ],
        [
            election.audit_name,
            election.audit_type,
            election.audit_math_type,
            f"{election.risk_limit}%",
            election.random_seed,
            pretty_boolean(election.online),
        ],
    ]


def audit_board_rows(election: Election):
    if not election.online:
        return None
    rows = [
        heading("AUDIT BOARDS"),
        [
            "Jurisdiction Name",
            "Audit Board Name",
            "Member 1 Name",
            "Member 1 Affiliation",
            "Member 2 Name",
            "Member 2 Affiliation",
        ],
    ]
    for jurisdiction in election.jurisdictions:
        for audit_board in jurisdiction.audit_boards:
            rows.append(
                [
                    jurisdiction.name,
                    audit_board.name,
                    audit_board.member_1,
                    pretty_affiliation(audit_board.member_1_affiliation),
                    audit_board.member_2,
                    pretty_affiliation(audit_board.member_2_affiliation),
                ]
            )
    return rows


def round_rows(election: Election):
    rows = [
        heading("ROUNDS"),
        [
            "Round Number",
            "Contest Name",
            "Targeted?",
            "Sample Size",
            "Risk Limit Met?",
            "P-Value",
            "Start Time",
            "End Time",
            "Audited Votes",
        ]
        + (
            ["Audited Votes: CVR", "Audited Votes: Non CVR"]
            if election.audit_type == AuditType.HYBRID
            else []
        )
        + (
            ["Batches Sampled", "Ballots Sampled", "Reported Votes"]
            if election.audit_type == AuditType.BATCH_COMPARISON
            else []
        ),
    ]

    round_contests = (
        RoundContest.query.join(Round)
        .filter_by(election_id=election.id)
        .join(Contest)
        .order_by(Round.round_num, Contest.created_at)
        .all()
    )
    for round_contest in round_contests:
        round = round_contest.round
        contest = round_contest.contest
        total_choice_votes = {
            choice.name: next(
                (
                    result.result
                    for result in round_contest.results
                    if result.contest_choice_id == choice.id
                ),
                0,
            )
            for choice in contest.choices
        }
        not_found_ballots = (
            samples_not_found_by_round(contest).get(round.id, 0)
            if election.audit_type == AuditType.BALLOT_POLLING and election.online
            else None
        )

        if election.audit_type == AuditType.HYBRID:
            # In hybrid audits, round contest results only store vote counts
            # for non-CVR ballots. So we compute the totals using the ballot
            # interpretations for the CVR ballots.
            non_cvr_choice_vote = total_choice_votes
            choice_id_to_name = {choice.id: choice.name for choice in contest.choices}
            cvr_choice_votes = Counter({choice.name: 0 for choice in contest.choices})
            for ballot in sampled_ballot_interpretations_to_cvrs(contest).values():
                choice_votes = ballot["cvr"] and ballot["cvr"].get(contest.id)  # type: ignore
                if choice_votes:
                    cvr_choice_votes.update(
                        {
                            choice_id_to_name[choice_id]: int(count)
                            for choice_id, count in choice_votes.items()
                        }
                    )
            total_choice_votes = Counter()
            total_choice_votes.update(non_cvr_choice_vote)
            total_choice_votes.update(cvr_choice_votes)

        if election.audit_type == AuditType.BATCH_COMPARISON:
            sampled_batches = (
                Batch.query.join(SampledBatchDraw)
                .join(Round)
                .join(Jurisdiction)
                .filter_by(election_id=election.id)
                .filter(SampledBatchDraw.round_id == round.id)
                .filter(SampledBatchDraw.ticket_number != EXTRA_TICKET_NUMBER)
                .all()
            )
            sampled_batch_ids = {batch.id for batch in sampled_batches}
            combined_sub_batches = (
                Batch.query.join(Jurisdiction)
                .filter_by(election_id=election.id)
                .filter(Batch.combined_batch_name.isnot(None))
                .all()
            )
            combined_batches_sampled_this_round = [
                combined_batch
                for combined_batch in group_combined_batches(combined_sub_batches)
                if any(
                    batch.id in sampled_batch_ids
                    for batch in combined_batch["sub_batches"]
                )
            ]

            # Ensure we only count each combined batch once
            uncombined_sampled_batches = [
                batch for batch in sampled_batches if not batch.combined_batch_name
            ]
            num_sampled_batches = len(uncombined_sampled_batches) + len(
                combined_batches_sampled_this_round
            )

            # To get the total ballots/reported results in the sampled batches,
            # we need to include all combined sub batches (even unsampled ones)
            for combined_batch in combined_batches_sampled_this_round:
                for sub_batch in combined_batch["sub_batches"]:
                    if sub_batch.id not in sampled_batch_ids:
                        sampled_batches.append(sub_batch)

            num_ballots_in_sampled_batches = sum(
                batch.num_ballots for batch in sampled_batches
            )

            # Get the reported votes aggregated across batches
            reported_results: dict = {choice.id: 0 for choice in contest.choices}
            for batch in sampled_batches:
                reported_results_for_batch = batch.jurisdiction.batch_tallies[
                    batch.name
                ].get(contest.id)
                if reported_results_for_batch is not None:
                    for choice in contest.choices:
                        reported_results[choice.id] += reported_results_for_batch[
                            choice.id
                        ]

            reported_results_by_name = {
                choice.name: reported_results[choice.id] for choice in contest.choices
            }

        rows.append(
            [
                round.round_num,
                contest.name,
                pretty_targeted(contest.is_targeted),
                round_contest.sample_size and round_contest.sample_size["size"],
                pretty_boolean(bool(round_contest.is_complete)),
                pretty_pvalue(round_contest.end_p_value),
                isoformat(round.created_at),
                isoformat(round.ended_at),
                pretty_choice_votes(total_choice_votes, not_found=not_found_ballots),
            ]
            + (
                [
                    pretty_choice_votes(dict(cvr_choice_votes)),
                    pretty_choice_votes(non_cvr_choice_vote),
                ]
                if election.audit_type == AuditType.HYBRID
                else []
            )
            + (
                [
                    num_sampled_batches,
                    num_ballots_in_sampled_batches,
                    pretty_choice_votes(reported_results_by_name),
                ]
                if election.audit_type == AuditType.BATCH_COMPARISON
                else []
            )
        )
    return rows


def full_hand_tally_result_rows(election: Election, jurisdiction: Jurisdiction = None):
    rows = [heading("FULL HAND TALLY BATCH RESULTS")]

    results_query = (
        FullHandTallyBatchResult.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .order_by(Jurisdiction.name, FullHandTallyBatchResult.batch_name)
    )
    if jurisdiction:
        results_query = results_query.filter(Jurisdiction.id == jurisdiction.id)
    results = list(
        results_query.with_entities(Jurisdiction.name, FullHandTallyBatchResult).all()
    )

    # For now, we only support one contest
    contest = list(election.contests)[0]
    results_by_batch: dict = defaultdict(
        lambda: {choice.id: None for choice in contest.choices}
    )
    for jurisdiction_name, result in results:
        results_by_batch[(jurisdiction_name, result.batch_name, result.batch_type)][
            result.contest_choice_id
        ] = result.result

    rows.append(
        ["Jurisdiction Name", "Batch Name", "Batch Type"]
        + [choice.name for choice in contest.choices]
    )

    for (
        (jurisdiction_name, batch_name, batch_type),
        choice_results,
    ) in results_by_batch.items():
        rows.append(
            [jurisdiction_name, batch_name, batch_type] + list(choice_results.values())
        )

    return rows


def sampled_ballot_rows(election: Election, jurisdiction: Jurisdiction = None):
    # Special case: if we sampled all ballots, don't show this section
    rounds = list(election.rounds)
    if len(rounds) > 0 and is_full_hand_tally(rounds[0], election):
        return full_hand_tally_result_rows(election, jurisdiction)

    rows = [heading("SAMPLED BALLOTS")]

    # In order to avoid loading all of the ballots into memory at once (there
    # may be 10-100k), we use yield_per(n), which streams n ballots at a
    # time from the database. There's a bunch of related data we want for each ballot
    # (e.g. imprinted id, ticket numbers, ballot interpretations), but we don't
    # want to make separate queries for each individual ballot's relationships.
    # Usually, you can use sqlalchemy's eager loading features to load this
    # data as part of the original query, but they don't work with yield_per.
    # So instead, we join in the data we need and return it in arrays.

    ballot_interpretation_selected_choices = (
        BallotInterpretation.query.join(BallotInterpretation.selected_choices)
        .group_by(BallotInterpretation.ballot_id, BallotInterpretation.contest_id)
        .with_entities(
            BallotInterpretation.ballot_id,
            BallotInterpretation.contest_id,
            func.array_agg(
                aggregate_order_by(ContestChoice.name, ContestChoice.created_at)
            ).label("selected_choice_names"),
        )
        .subquery()
    )
    ballot_interpretations = (
        BallotInterpretation.query.outerjoin(
            ballot_interpretation_selected_choices,
            and_(
                BallotInterpretation.ballot_id
                == ballot_interpretation_selected_choices.c.ballot_id,
                BallotInterpretation.contest_id
                == ballot_interpretation_selected_choices.c.contest_id,
            ),
        )
        .group_by(
            BallotInterpretation.ballot_id,
        )
        .with_entities(
            BallotInterpretation.ballot_id,
            func.array_agg(
                func.json_build_array(
                    BallotInterpretation.contest_id,
                    BallotInterpretation.interpretation,
                    ballot_interpretation_selected_choices.c.selected_choice_names,
                    BallotInterpretation.comment,
                    BallotInterpretation.is_overvote,
                    BallotInterpretation.has_invalid_write_in,
                )
            ).label("interpretations"),
        )
        .subquery()
    )

    ticket_numbers = (
        SampledBallotDraw.query.join(Round)
        .group_by(SampledBallotDraw.ballot_id)
        .with_entities(
            SampledBallotDraw.ballot_id,
            func.array_agg(
                func.json_build_array(
                    Round.round_num,
                    SampledBallotDraw.contest_id,
                    SampledBallotDraw.ticket_number,
                )
            ).label("ticket_numbers"),
        )
        .subquery()
    )

    imprinted_ids = (
        SampledBallot.query.join(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .with_entities(SampledBallot.id, CvrBallot.imprinted_id)
        .subquery()
    )

    min_round_num = (
        SampledBallotDraw.query.join(Round)
        .order_by(SampledBallotDraw.ballot_id, Round.round_num)
        .distinct(SampledBallotDraw.ballot_id)
        .with_entities(SampledBallotDraw.ballot_id, Round.round_num)
        .subquery()
    )

    ballots = (
        SampledBallot.query.join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .join(min_round_num)
        .order_by(
            min_round_num.c.round_num,
            Jurisdiction.name,
            func.human_sort(Batch.container),
            func.human_sort(Batch.tabulator),
            func.human_sort(Batch.name),
            SampledBallot.ballot_position,
        )
    )
    if jurisdiction:
        ballots = ballots.filter(Jurisdiction.id == jurisdiction.id)
    ballots = (
        ballots.join(ticket_numbers)
        .outerjoin(imprinted_ids, SampledBallot.id == imprinted_ids.c.id)
        .outerjoin(
            ballot_interpretations,
            SampledBallot.id == ballot_interpretations.c.ballot_id,
        )
        .with_entities(
            SampledBallot,
            Batch,
            Jurisdiction.name,
            imprinted_ids.c.imprinted_id,
            ticket_numbers.c.ticket_numbers,
            func.coalesce(ballot_interpretations.c.interpretations, []),
        )
        .yield_per(100)  # Experimentally, 100 seems to be faster than 10 or 1000
    )

    targeted_contests = [
        contest for contest in election.contests if contest.is_targeted
    ]

    one_batch = (
        Batch.query.join(Jurisdiction).filter_by(election_id=election.id).first()
    )
    show_container = one_batch and one_batch.container is not None
    show_tabulator = one_batch and one_batch.tabulator is not None
    show_cvrs = election.audit_type in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]

    is_ballot_comparison = election.audit_type == AuditType.BALLOT_COMPARISON
    if is_ballot_comparison:
        show_discrepancies_by_jurisdiction = (
            show_ballot_comparison_discrepancies_by_jurisdiction(election, rounds[-1])
        )

    result_columns = []
    if election.online:
        result_columns.append("Audited?")
        for contest in election.contests:
            result_columns.append(f"Audit Result: {contest.name}")
            if show_cvrs:
                result_columns.append(f"CVR Result: {contest.name}")
                result_columns.append(f"Change in Results: {contest.name}")
                result_columns.append(f"Change in Margin: {contest.name}")

    rows.append(
        ["Jurisdiction Name"]
        + (["Container"] if show_container else [])
        + (["Tabulator"] if show_tabulator else [])
        + ["Batch Name", "Ballot Position"]
        + (["Imprinted ID"] if show_cvrs else [])
        + [f"Ticket Numbers: {contest.name}" for contest in targeted_contests]
        + result_columns
    )

    if show_cvrs:
        cvrs_by_contest = {
            contest.id: cvrs_for_contest(contest) for contest in election.contests
        }
        audited_cvrs_by_contest = {
            contest.id: sampled_ballot_interpretations_to_cvrs(contest)
            for contest in election.contests
        }
        discrepancies_by_contest = {
            contest.id: supersimple.compute_discrepancies(
                sampler_contest.from_db_contest(contest),
                cvrs_by_contest[contest.id],
                audited_cvrs_by_contest[contest.id],
            )
            for contest in election.contests
        }

    for ballot in ballots:
        (
            ballot,
            batch,
            jurisdiction_name,
            imprinted_id,
            ticket_numbers,
            interpretations,
        ) = ballot

        result_values = []
        if election.online:
            if (
                is_ballot_comparison
                and not show_discrepancies_by_jurisdiction[batch.jurisdiction_id]
            ):
                result_values = ["NOT_AUDITED"] + ([""] * (len(result_columns) - 1))
            else:
                result_values.append(ballot.status)
                for contest in election.contests:
                    result_values.append(
                        pretty_ballot_interpretation(interpretations, contest)
                    )
                    if show_cvrs:
                        cvr_interpretation = pretty_cvr_interpretation(
                            ballot, contest, cvrs_by_contest[contest.id]
                        )
                        result_values.append(cvr_interpretation)
                        audited_result = audited_cvrs_by_contest[contest.id].get(
                            ballot.id
                        )
                        vote_deltas = audited_result and ballot_vote_deltas(
                            contest,
                            cvrs_by_contest[contest.id].get(ballot.id),
                            audited_result["cvr"],
                        )
                        result_values.append(pretty_vote_deltas(contest, vote_deltas))
                        result_values.append(
                            pretty_discrepancy(
                                ballot, discrepancies_by_contest[contest.id]
                            )
                        )

        rows.append(
            [jurisdiction_name]
            + ([batch.container] if show_container else [])
            + ([batch.tabulator] if show_tabulator else [])
            + [
                batch.name,
                ballot.ballot_position,
            ]
            + ([imprinted_id] if show_cvrs else [])
            + pretty_ballot_ticket_numbers(ticket_numbers, targeted_contests)
            + result_values
        )
    return rows


def sampled_batch_rows(election: Election, jurisdiction: Jurisdiction = None):
    rows = [heading("SAMPLED BATCHES")]

    batches_query = (
        Batch.query.join(SampledBatchDraw)
        .join(Round)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
    )
    if jurisdiction:
        batches_query = batches_query.filter(Jurisdiction.id == jurisdiction.id)

    batches = batches_query.order_by(
        Round.round_num,
        Jurisdiction.name,
        func.human_sort(Batch.name),
        SampledBatchDraw.ticket_number,
    ).all()

    round_id_to_num = {round.id: round.round_num for round in election.rounds}

    audit_result_tuples = (
        BatchResultTallySheet.query.filter(
            BatchResultTallySheet.batch_id.in_(
                batches_query.with_entities(Batch.id).subquery()
            )
        )
        .join(BatchResult)
        .group_by(BatchResultTallySheet.batch_id, BatchResult.contest_choice_id)
        .values(
            BatchResultTallySheet.batch_id,
            BatchResult.contest_choice_id,
            func.sum(BatchResult.result),
        )
    )
    audit_results_by_batch = {
        batch_id: {choice_id: result for _, choice_id, result in choice_results}
        for batch_id, choice_results in group_by(
            audit_result_tuples, lambda tuple: tuple[0]
        ).items()
    }

    combined_sub_batches = (
        Batch.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .filter(Jurisdiction.id == jurisdiction.id if jurisdiction else True)
        .filter(Batch.combined_batch_name.isnot(None))
        .all()
    )
    combined_batches = group_combined_batches(combined_sub_batches)
    combined_sub_batch_ids = {batch.id for batch in combined_sub_batches}
    has_combined_batches = len(combined_batches) > 0

    contests = list(
        election.contests if jurisdiction is None else jurisdiction.contests
    )

    ticket_number_columns = []
    result_columns = []
    for contest in contests:
        ticket_number_columns += [f"Ticket Numbers: {contest.name}"]
        result_columns += [
            f"Audit Results: {contest.name}",
            f"Reported Results: {contest.name}",
            f"Change in Results: {contest.name}",
            f"Change in Margin: {contest.name}",
        ]
    column_headers = [
        "Jurisdiction Name",
        "Batch Name",
        "Ballots in Batch",
        *ticket_number_columns,
        "Audited?",
        *result_columns,
        "Last Edited By",
    ]
    if has_combined_batches:
        column_headers.append("Combined Batch")
    rows.append(column_headers)

    total_reported_results: dict = {
        contest.id: {choice.id: 0 for choice in contest.choices} for contest in contests
    }
    total_audit_results: dict = {
        contest.id: {choice.id: 0 for choice in contest.choices} for contest in contests
    }

    show_discrepancies_by_jurisdiction = (
        show_batch_comparison_discrepancies_by_jurisdiction(election)
    )

    for batch in batches:
        row = [
            batch.jurisdiction.name,
            batch.name,
            batch.num_ballots,
            *pretty_batch_ticket_numbers(batch, round_id_to_num, contests),
        ]
        if not show_discrepancies_by_jurisdiction[batch.jurisdiction.id]:
            row += [pretty_boolean(False)]
            row += [""] * (len(result_columns) + 1)
            rows.append(row)
            continue

        is_audited = batch.id in audit_results_by_batch
        row += [pretty_boolean(is_audited)]

        is_combined = batch.id in combined_sub_batch_ids

        for contest in contests:
            reported_results = batch.jurisdiction.batch_tallies[batch.name].get(
                contest.id
            )
            if reported_results is not None:
                # For combined batches, we need to add the combined batch
                # reported results to the total, since it may include some
                # unsampled batches. We add these below, so we skip them here.
                if not is_combined:
                    for choice in contest.choices:
                        total_reported_results[contest.id][
                            choice.id
                        ] += reported_results[choice.id]

            reported_results_by_name = reported_results and {
                choice.name: reported_results[choice.id] for choice in contest.choices
            }

            audit_results = (
                {
                    choice.id: audit_results_by_batch[batch.id].get(choice.id, 0)
                    for choice in contest.choices
                }
                if is_audited and reported_results
                else None
            )
            if audit_results is not None:
                for choice in contest.choices:
                    total_audit_results[contest.id][choice.id] += audit_results[
                        choice.id
                    ]
            audit_results_by_name = audit_results and {
                choice.name: audit_results[choice.id] for choice in contest.choices
            }

            error = (
                macro.compute_error(
                    {contest.id: reported_results},
                    {contest.id: audit_results},
                    sampler_contest.from_db_contest(contest),
                    0,
                )
                if is_audited and audit_results and not is_combined
                else None
            )

            row += [
                (
                    pretty_choice_votes(audit_results_by_name)
                    if audit_results_by_name and not is_combined
                    else ""
                ),
                (
                    pretty_choice_votes(reported_results_by_name)
                    if reported_results_by_name
                    else ""
                ),
                (
                    pretty_vote_deltas(
                        contest, batch_vote_deltas(reported_results, audit_results)
                    )
                    if reported_results and audit_results and not is_combined
                    else ""
                ),
                error["counted_as"] if error else "",
            ]

        row += [construct_batch_last_edited_by_string(batch)]
        if has_combined_batches:
            row.append(batch.combined_batch_name or "")

        rows.append(row)

    if has_combined_batches:
        for combined_batch in combined_batches:
            representative_batch = combined_batch["representative_batch"]
            sub_batches = combined_batch["sub_batches"]
            is_audited = representative_batch.id in audit_results_by_batch
            combined_batch_row = [
                representative_batch.jurisdiction.name,
                representative_batch.combined_batch_name,
                sum(batch.num_ballots for batch in sub_batches),
                "",  # Ticket number cols - not relevant to combined batches
                pretty_boolean(is_audited),
            ]
            for contest in contests:
                sub_batch_reported_results = list(
                    sub_batch.jurisdiction.batch_tallies[sub_batch.name].get(contest.id)  # type: ignore
                    for sub_batch in sub_batches
                )
                reported_results = {
                    choice.id: sum(
                        reported_results[choice.id]
                        for reported_results in sub_batch_reported_results
                        if reported_results is not None
                    )
                    for choice in contest.choices
                }
                for choice in contest.choices:
                    total_reported_results[contest.id][choice.id] += reported_results[
                        choice.id
                    ]

                reported_results_by_name = {
                    choice.name: reported_results[choice.id]
                    for choice in contest.choices
                }

                audit_results = (
                    {
                        choice.id: audit_results_by_batch[representative_batch.id].get(
                            choice.id, 0
                        )
                        for choice in contest.choices
                    }
                    if is_audited
                    else None
                )
                audit_results_by_name = audit_results and {
                    choice.name: audit_results[choice.id] for choice in contest.choices
                }

                error = (
                    macro.compute_error(
                        {contest.id: reported_results},
                        {contest.id: audit_results},
                        sampler_contest.from_db_contest(contest),
                        0,
                    )
                    if audit_results
                    else None
                )

                combined_batch_row += [
                    (
                        pretty_choice_votes(audit_results_by_name)
                        if audit_results_by_name
                        else ""
                    ),
                    pretty_choice_votes(reported_results_by_name),
                    (
                        pretty_vote_deltas(
                            contest,
                            batch_vote_deltas(reported_results, audit_results),
                        )
                        if audit_results
                        else ""
                    ),
                    error["counted_as"] if error else "",
                ]

            combined_batch_row += [
                construct_batch_last_edited_by_string(representative_batch),
                f"Combines {', '.join(sub_batch.name for sub_batch in sorted(sub_batches, key=lambda batch: batch.name))}",
            ]
            rows.append(combined_batch_row)

    totals_row = ["Totals", "", sum(batch.num_ballots for batch in batches)]
    totals_row += ["" for _ in contests]  # Ticket number cols - not relevant to totals
    totals_row += [""]  # Audited flag - not relevant to totals
    for contest in contests:
        total_reported_results_by_name = {
            choice.name: total_reported_results[contest.id][choice.id]
            for choice in contest.choices
        }
        total_audit_results_by_name = {
            choice.name: total_audit_results[contest.id][choice.id]
            for choice in contest.choices
        }
        totals_row += [
            pretty_choice_votes(total_audit_results_by_name),
            pretty_choice_votes(total_reported_results_by_name),
            "",  # change in results not calculated for totals
            "",  # change in margin not calculated for totals
        ]
    totals_row += ""  # last edited col
    rows.append(totals_row)
    return rows


@api.route("/election/<election_id>/report", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def audit_admin_audit_report(election: Election):
    if len(list(election.rounds)) == 0:
        raise Conflict("Cannot generate report until audit starts")

    row_sets = [
        election_info_rows(election),
        contest_rows(election),
        contest_name_standardization_rows(election),
        audit_settings_rows(election),
        audit_board_rows(election),
        round_rows(election),
        (
            sampled_batch_rows(election)
            if election.audit_type == AuditType.BATCH_COMPARISON
            else sampled_ballot_rows(election)
        ),
    ]
    row_sets = [row_set for row_set in row_sets if row_set]

    csv_io = io.StringIO()
    report = csv.writer(csv_io)

    for row_set in row_sets[:-1]:
        report.writerows(row_set)
        report.writerow([])
    report.writerows(row_sets[-1])

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"audit-report-{election_timestamp_name(election)}.csv",
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/report", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def jursdiction_admin_audit_report(election: Election, jurisdiction: Jurisdiction):
    if len(list(election.rounds)) == 0:
        raise Conflict("Cannot generate report until audit starts")

    csv_io = io.StringIO()
    report = csv.writer(csv_io)

    report.writerows(
        (
            sampled_batch_rows(election, jurisdiction)
            if election.audit_type == AuditType.BATCH_COMPARISON
            else sampled_ballot_rows(election, jurisdiction)
        ),
    )

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"audit-report-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
    )


@api.route("/election/<election_id>/discrepancy-report", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def audit_admin_discrepancy_report(election: Election):
    if len(list(election.rounds)) == 0:
        raise Conflict("Cannot generate report until audit starts")

    if election.audit_type == AuditType.BALLOT_COMPARISON:
        rows = sampled_ballot_rows(election)
    elif election.audit_type == AuditType.BATCH_COMPARISON:
        rows = sampled_batch_rows(election)
    else:
        raise BadRequest("Discrepancy report not supported for this audit type")

    csv_io = io.StringIO()
    report = csv.writer(csv_io)
    report.writerows(
        rows[1:]  # Remove section heading, since this report only has one section
    )

    csv_io.seek(0)
    return csv_response(
        csv_io,
        filename=f"discrepancy-report-{election_timestamp_name(election)}.csv",
    )
