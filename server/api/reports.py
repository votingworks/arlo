import io, csv
from typing import Dict, List

from . import api
from ..models import *  # pylint: disable=wildcard-import
from ..auth import with_election_access, with_jurisdiction_access
from ..util.csv_download import csv_response, election_timestamp_name
from ..util.isoformat import isoformat
from ..util.group_by import group_by


def pretty_affiliation(affiliation: Affiliation) -> str:
    mapping = {
        Affiliation.DEMOCRAT: "Democrat",
        Affiliation.REPUBLICAN: "Republican",
        Affiliation.LIBERTARIAN: "Libertarian",
        Affiliation.INDEPENDENT: "Independent",
        Affiliation.OTHER: "Other",
    }
    return mapping.get(affiliation, "")


def pretty_boolean(boolean: bool) -> str:
    return "Yes" if boolean else "No"


def pretty_targeted(is_targeted: bool) -> str:
    return "Targeted" if is_targeted else "Opportunistic"


def pretty_ticket_numbers(
    ballot: SampledBallot, round_id_to_num: Dict[str, int]
) -> str:
    ticket_numbers = []
    for round_num, draws in group_by(
        ballot.draws, key=lambda d: round_id_to_num[d.round_id]
    ).items():
        ticket_numbers_str = ", ".join(sorted(d.ticket_number for d in draws))
        ticket_numbers.append(f"Round {round_num}: {ticket_numbers_str}")
    return ", ".join(ticket_numbers)


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


def write_heading(report, heading: str):
    report.writerow([f"######## {heading} ########"])


def write_election_info(report, election: Election):
    write_heading(report, "ELECTION INFO")
    report.writerow(["Election Name", "State"])
    report.writerow([election.election_name, election.state])


def write_contests(report, election: Election):
    write_heading(report, "CONTESTS")
    report.writerow(
        [
            "Contest Name",
            "Targeted?",
            "Number of Winners",
            "Votes Allowed",
            "Total Ballots Cast",
            "Tabulated Votes",
        ]
    )
    for contest in election.contests:
        choices = "; ".join(
            [f"{choice.name}: {choice.num_votes}" for choice in contest.choices]
        )
        report.writerow(
            [
                contest.name,
                pretty_targeted(contest.is_targeted),
                contest.num_winners,
                contest.votes_allowed,
                contest.total_ballots_cast,
                choices,
            ]
        )


def write_audit_settings(report, election: Election):
    write_heading(report, "AUDIT SETTINGS")
    report.writerow(["Audit Name", "Risk Limit", "Random Seed", "Online Data Entry?"])
    report.writerow(
        [
            election.audit_name,
            f"{election.risk_limit}%",
            election.random_seed,
            pretty_boolean(election.online),
        ]
    )


def write_audit_boards(report, election: Election):
    if election.online:
        write_heading(report, "AUDIT BOARDS")
        report.writerow(
            [
                "Jurisdiction Name",
                "Audit Board Name",
                "Member 1 Name",
                "Member 1 Affiliation",
                "Member 2 Name",
                "Member 2 Affiliation",
            ]
        )
        for jurisdiction in election.jurisdictions:
            for audit_board in jurisdiction.audit_boards:
                report.writerow(
                    [
                        jurisdiction.name,
                        audit_board.name,
                        audit_board.member_1,
                        pretty_affiliation(
                            Affiliation(audit_board.member_1_affiliation)
                        ),
                        audit_board.member_2,
                        pretty_affiliation(
                            Affiliation(audit_board.member_2_affiliation)
                        ),
                    ]
                )


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


def write_rounds(report, election: Election):
    write_heading(report, "ROUNDS")
    report.writerow(
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
    )
    for round in election.rounds:
        for contest in election.contests:
            round_contest = next(
                rc for rc in round.round_contests if rc.contest_id == contest.id
            )
            report.writerow(
                [
                    round.round_num,
                    contest.name,
                    pretty_targeted(contest.is_targeted),
                    round_contest.sample_size,
                    pretty_boolean(bool(round_contest.is_complete)),
                    round_contest.end_p_value,
                    isoformat(round.created_at),
                    isoformat(round.ended_at),
                    pretty_audited_votes(contest, round_contest),
                ]
            )


def write_sampled_ballots(
    report, election: Election, jurisdiction: Jurisdiction = None
):
    write_heading(report, "SAMPLED BALLOTS")

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

    report.writerow(
        [
            "Jurisdiction Name",
            "Batch Name",
            "Ballot Position",
            "Ticket Numbers",
            "Audited?",
        ]
        + [f"Audit Result: {contest.name}" for contest in election.contests]
    )
    for ballot in ballots:
        report.writerow(
            [
                ballot.batch.jurisdiction.name,
                ballot.batch.name,
                ballot.ballot_position,
                pretty_ticket_numbers(ballot, round_id_to_num),
                ballot.status,
            ]
            + pretty_interpretations(
                list(ballot.interpretations), list(election.contests)
            )
        )


@api.route("/election/<election_id>/report", methods=["GET"])
@with_election_access
def audit_admin_audit_report(election: Election):
    csv_io = io.StringIO()
    report = csv.writer(csv_io)

    write_election_info(report, election)
    report.writerow([])
    write_contests(report, election)
    report.writerow([])
    write_audit_settings(report, election)
    report.writerow([])
    write_audit_boards(report, election)
    report.writerow([])
    write_rounds(report, election)
    report.writerow([])
    write_sampled_ballots(report, election)

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

    write_sampled_ballots(report, election, jurisdiction)

    return csv_response(
        csv_io.getvalue(),
        filename=f"audit-report-{election_timestamp_name(election)}.csv",
    )
