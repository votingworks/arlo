import io, csv
from typing import Dict, List, Optional
from collections import defaultdict
from sqlalchemy.orm import joinedload, contains_eager

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType
from ..util.csv_download import (
    csv_response,
    election_timestamp_name,
    jurisdiction_timestamp_name,
)
from ..util.isoformat import isoformat
from ..util.group_by import group_by
from ..audit_math import supersimple, sampler_contest
from ..api.rounds import (
    cvrs_for_contest,
    sampled_ballot_interpretations_to_cvrs,
    sampled_all_ballots,
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
    elif value < 10 ** -10:
        return "<0.0000000001"
    else:
        ret = "{:1.10f}".format(round(value, 10)).rstrip("0")
        # If we've stripped off the zero right after the decimal, put it back
        if ret[-1] == ".":
            ret += "0"
        return ret


def pretty_ballot_ticket_numbers(
    ballot: SampledBallot,
    round_id_to_num: Dict[str, int],
    targeted_contests: List[Contest],
) -> List[str]:
    columns = []
    for contest in targeted_contests:
        contest_draws = [draw for draw in ballot.draws if draw.contest_id == contest.id]
        ticket_numbers = []
        for round_num, draws in group_by(
            contest_draws, key=lambda d: round_id_to_num[d.round_id]
        ).items():
            ticket_numbers_str = ", ".join(sorted(d.ticket_number for d in draws))
            ticket_numbers.append(f"Round {round_num}: {ticket_numbers_str}")
        columns.append(", ".join(ticket_numbers))
    return columns


def pretty_batch_ticket_numbers(batch: Batch, round_id_to_num: Dict[str, int]) -> str:
    ticket_numbers = []
    for round_num, draws in group_by(
        list(batch.draws), key=lambda d: round_id_to_num[d.round_id]
    ).items():
        ticket_numbers_str = ", ".join(sorted(d.ticket_number for d in draws))
        ticket_numbers.append(f"Round {round_num}: {ticket_numbers_str}")
    return ", ".join(ticket_numbers)


def pretty_ballot_interpretation(
    interpretations: List[BallotInterpretation], contest: Contest,
) -> str:
    interpretation = next(
        (i for i in interpretations if i.contest_id == contest.id), None,
    )
    # Legacy case: we used to not require an interpretation for every contest
    # before we had Interpretation.CONTEST_NOT_ON_BALLOT
    if not interpretation:
        return ""

    choices = (
        ", ".join(choice.name for choice in interpretation.selected_choices)
        if interpretation.interpretation == Interpretation.VOTE
        else interpretation.interpretation
    )
    overvote = "OVERVOTE; " if interpretation.is_overvote else ""
    comment = f"; COMMENT: {interpretation.comment}" if interpretation.comment else ""
    return overvote + choices + comment


def pretty_cvr_interpretation(
    ballot: SampledBallot, contest: Contest, contest_cvrs: supersimple.CVRS
) -> str:
    ballot_cvr = contest_cvrs[ballot.id]
    assert ballot_cvr is not None

    cvrs_by_choice = ballot_cvr.get(contest.id)
    # If CVR was empty for this contest for this ballot, skip it
    if not cvrs_by_choice:
        return ""

    choice_id_to_name = {choice.id: choice.name for choice in contest.choices}
    return ", ".join(
        choice_id_to_name[choice_id]
        for choice_id, interpretation in cvrs_by_choice.items()
        if interpretation == 1
    )


def pretty_discrepancy(
    ballot: SampledBallot, contest_discrepancies: Dict[str, supersimple.Discrepancy],
) -> str:
    if ballot.id in contest_discrepancies:
        return str(contest_discrepancies[ballot.id]["counted_as"])
    else:
        return ""


def pretty_batch_results(batch: Batch, contest: Contest) -> str:
    choice_votes = []
    for choice in contest.choices:
        choice_result = next(
            (
                result.result
                for result in batch.results
                if result.contest_choice_id == choice.id
            ),
            0,
        )
        choice_votes.append(f"{choice.name}: {choice_result}")
    return "; ".join(choice_votes)


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
            "Tabulated Votes",
        ],
    ]

    for contest in election.contests:
        choices = "; ".join(
            [f"{choice.name}: {choice.num_votes}" for choice in contest.choices]
        )
        rows.append(
            [
                contest.name,
                pretty_targeted(contest.is_targeted),
                contest.num_winners,
                contest.votes_allowed,
                contest.total_ballots_cast,
                choices,
            ]
        )
    return rows


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


def pretty_audited_votes(contest: Contest, round_contest: RoundContest):
    choice_votes = []
    for choice in contest.choices:
        choice_result = next(
            (
                result.result
                for result in round_contest.results
                if result.contest_choice_id == choice.id
            ),
            0,
        )
        choice_votes.append(f"{choice.name}: {choice_result}")
    return "; ".join(choice_votes)


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
        ],
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
        rows.append(
            [
                round.round_num,
                contest.name,
                pretty_targeted(contest.is_targeted),
                round_contest.sample_size,
                pretty_boolean(bool(round_contest.is_complete)),
                pretty_pvalue(round_contest.end_p_value),
                isoformat(round.created_at),
                isoformat(round.ended_at),
                pretty_audited_votes(contest, round_contest),
            ]
        )
    return rows


def offline_batch_result_rows(election: Election, jurisdiction: Jurisdiction = None):
    rows = [heading("BATCH RESULTS")]

    results_query = (
        OfflineBatchResult.query.join(Jurisdiction)
        .filter_by(election_id=election.id)
        .order_by(Jurisdiction.name, OfflineBatchResult.batch_name)
    )
    if jurisdiction:
        results_query = results_query.filter(Jurisdiction.id == jurisdiction.id)
    results = list(
        results_query.with_entities(Jurisdiction.name, OfflineBatchResult).all()
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
    if len(rounds) > 0 and sampled_all_ballots(rounds[0], election):
        return offline_batch_result_rows(election, jurisdiction)

    rows = [heading("SAMPLED BALLOTS")]

    ballots_query = (
        SampledBallot.query.join(SampledBallotDraw)
        .join(Round)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .outerjoin(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .order_by(
            Round.round_num,
            Jurisdiction.name,
            Batch.container,
            Batch.tabulator,
            Batch.name,
            SampledBallot.ballot_position,
        )
    )
    if jurisdiction:
        ballots_query = ballots_query.filter(Jurisdiction.id == jurisdiction.id)
    ballots = list(
        ballots_query.with_entities(SampledBallot, CvrBallot.imprinted_id)
        .options(
            contains_eager(SampledBallot.batch)
            .contains_eager(Batch.jurisdiction)
            .load_only(Jurisdiction.name),
            contains_eager(SampledBallot.draws).load_only(
                SampledBallotDraw.ticket_number
            ),
            joinedload(SampledBallot.interpretations)
            .joinedload(BallotInterpretation.selected_choices)
            .load_only(ContestChoice.name),
        )
        .all()
    )

    round_id_to_num = {round.id: round.round_num for round in election.rounds}

    targeted_contests = [
        contest for contest in election.contests if contest.is_targeted
    ]

    show_tabulator = len(ballots) > 0 and ballots[0][0].batch.tabulator is not None
    show_container = len(ballots) > 0 and ballots[0][0].batch.container is not None
    show_imprinted_id = len(ballots) > 0 and ballots[0][1] is not None
    show_cvrs = election.audit_type == AuditType.BALLOT_COMPARISON

    result_columns = []
    if election.online:
        for contest in election.contests:
            result_columns.append(f"Audit Result: {contest.name}")
            if show_cvrs:
                result_columns.append(f"CVR Result: {contest.name}")
                result_columns.append(f"Discrepancy: {contest.name}")

    rows.append(
        ["Jurisdiction Name"]
        + (["Container"] if show_container else [])
        + (["Tabulator"] if show_tabulator else [])
        + ["Batch Name", "Ballot Position"]
        + (["Imprinted ID"] if show_imprinted_id else [])
        + [f"Ticket Numbers: {contest.name}" for contest in targeted_contests]
        + (["Audited?"] if election.online else [])
        + result_columns
    )

    if show_cvrs:
        cvrs_by_contest = {
            contest.id: cvrs_for_contest(contest) for contest in election.contests
        }
        discrepancies_by_contest = {
            contest.id: supersimple.compute_discrepancies(
                sampler_contest.from_db_contest(contest),
                cvrs_by_contest[contest.id],
                sampled_ballot_interpretations_to_cvrs(contest),
            )
            for contest in election.contests
        }

    for ballot, imprinted_id in ballots:
        result_values = []
        if election.online:
            for contest in election.contests:
                result_values.append(
                    pretty_ballot_interpretation(list(ballot.interpretations), contest)
                )
                if show_cvrs:
                    cvr_interpretation = pretty_cvr_interpretation(
                        ballot, contest, cvrs_by_contest[contest.id]
                    )
                    result_values.append(cvr_interpretation)
                    result_values.append(
                        pretty_discrepancy(ballot, discrepancies_by_contest[contest.id])
                    )

        rows.append(
            [ballot.batch.jurisdiction.name]
            + ([ballot.batch.container] if show_container else [])
            + ([ballot.batch.tabulator] if show_tabulator else [])
            + [ballot.batch.name, ballot.ballot_position]
            + ([imprinted_id] if show_imprinted_id else [])
            + pretty_ballot_ticket_numbers(ballot, round_id_to_num, targeted_contests)
            + ([ballot.status] if election.online else [])
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
        .order_by(
            Round.round_num,
            Jurisdiction.name,
            Batch.name,
            SampledBatchDraw.ticket_number,
        )
    )
    if jurisdiction:
        batches_query = batches_query.filter(Jurisdiction.id == jurisdiction.id)
    batches = batches_query.all()

    round_id_to_num = {round.id: round.round_num for round in election.rounds}

    # We only support one contest for batch audits
    assert len(list(election.contests)) == 1
    contest = list(election.contests)[0]
    rows.append(
        [
            "Jurisdiction Name",
            "Batch Name",
            "Ticket Numbers",
            "Audited?",
            "Audit Result",
        ]
    )
    for batch in batches:
        rows.append(
            [
                batch.jurisdiction.name,
                batch.name,
                pretty_batch_ticket_numbers(batch, round_id_to_num),
                pretty_boolean(len(batch.results) > 0),
                pretty_batch_results(batch, contest),
            ]
        )
    return rows


@api.route("/election/<election_id>/report", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def audit_admin_audit_report(election: Election):
    row_sets = [
        election_info_rows(election),
        contest_rows(election),
        audit_settings_rows(election),
        audit_board_rows(election),
        round_rows(election),
        sampled_batch_rows(election)
        if election.audit_type == AuditType.BATCH_COMPARISON
        else sampled_ballot_rows(election),
    ]
    row_sets = [row_set for row_set in row_sets if row_set]

    with io.StringIO() as csv_io:
        report = csv.writer(csv_io)

        for row_set in row_sets[:-1]:
            report.writerows(row_set)
            report.writerow([])
        report.writerows(row_sets[-1])

        return csv_response(
            csv_io.getvalue(),
            filename=f"audit-report-{election_timestamp_name(election)}.csv",
        )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/report", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def jursdiction_admin_audit_report(election: Election, jurisdiction: Jurisdiction):
    with io.StringIO() as csv_io:
        report = csv.writer(csv_io)

        report.writerows(
            sampled_batch_rows(election, jurisdiction)
            if election.audit_type == AuditType.BATCH_COMPARISON
            else sampled_ballot_rows(election, jurisdiction),
        )

        return csv_response(
            csv_io.getvalue(),
            filename=f"audit-report-{jurisdiction_timestamp_name(election, jurisdiction)}.csv",
        )
