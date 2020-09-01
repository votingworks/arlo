import io, csv
from typing import Dict, List, Optional

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access, with_jurisdiction_access
from ..util.csv_download import csv_response, election_timestamp_name
from ..util.isoformat import isoformat
from ..util.group_by import group_by


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
    elif value < 10 ** -10:
        return "<0.0000000001"
    else:
        ret = "{:1.10f}".format(round(value, 10)).rstrip("0")
        if ret[-1] == ".":
            ret += "0"  # If we've stripped off the zero right after the decimal, put it back
        return ret


def pretty_ticket_numbers(
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


def pretty_interpretations(
    interpretations: List[BallotInterpretation], contests: List[Contest],
) -> List[str]:
    columns = []
    for contest in contests:
        interpretation = next(
            (i for i in interpretations if i.contest_id == contest.id), None,
        )
        if interpretation:
            choices = (
                ", ".join(choice.name for choice in interpretation.selected_choices)
                if interpretation.interpretation == Interpretation.VOTE
                else interpretation.interpretation
            )
            overvote = "OVERVOTE; " if interpretation.is_overvote else ""
            comment = (
                f"; COMMENT: {interpretation.comment}" if interpretation.comment else ""
            )
            columns.append(overvote + choices + comment)
        else:
            columns.append("")
    return columns


def heading(heading: str):
    return [f"######## {heading} ########"]


def election_info_rows(election: Election):
    return [
        heading("ELECTION INFO"),
        ["Election Name", "State"],
        [election.election_name, election.state],
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
        ["Audit Name", "Risk Limit", "Random Seed", "Online Data Entry?"],
        [
            election.audit_name,
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


def sampled_ballot_rows(election: Election, jurisdiction: Jurisdiction = None):
    rows = [heading("SAMPLED BALLOTS")]

    ballots_query = (
        SampledBallot.query.join(SampledBallotDraw)
        .join(Round)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election.id)
        .order_by(
            Round.round_num,
            Jurisdiction.name,
            Batch.name,
            SampledBallot.ballot_position,
        )
    )
    if jurisdiction:
        ballots_query = ballots_query.filter(Jurisdiction.id == jurisdiction.id)
    ballots = ballots_query.all()

    round_id_to_num = {round.id: round.round_num for round in election.rounds}

    targeted_contests = [
        contest for contest in election.contests if contest.is_targeted
    ]
    rows.append(
        ["Jurisdiction Name", "Batch Name", "Ballot Position"]
        + [f"Ticket Numbers: {contest.name}" for contest in targeted_contests]
        + (
            ["Audited?"]
            + [f"Audit Result: {contest.name}" for contest in election.contests]
            if election.online
            else []
        )
    )
    for ballot in ballots:
        rows.append(
            [ballot.batch.jurisdiction.name, ballot.batch.name, ballot.ballot_position,]
            + pretty_ticket_numbers(ballot, round_id_to_num, targeted_contests)
            + (
                [ballot.status]
                + pretty_interpretations(
                    list(ballot.interpretations), list(election.contests)
                )
                if election.online
                else []
            )
        )
    return rows


@api.route("/election/<election_id>/report", methods=["GET"])
@with_election_access
def audit_admin_audit_report(election: Election):
    row_sets = [
        election_info_rows(election),
        contest_rows(election),
        audit_settings_rows(election),
        audit_board_rows(election),
        round_rows(election),
        sampled_ballot_rows(election),
    ]
    row_sets = [row_set for row_set in row_sets if row_set]

    csv_io = io.StringIO()
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
@with_jurisdiction_access
def jursdiction_admin_audit_report(election: Election, jurisdiction: Jurisdiction):
    csv_io = io.StringIO()
    report = csv.writer(csv_io)

    report.writerows(sampled_ballot_rows(election, jurisdiction))

    return csv_response(
        csv_io.getvalue(),
        filename=f"audit-report-{election_timestamp_name(election)}.csv",
    )
