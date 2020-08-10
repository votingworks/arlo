from typing import List, Optional
from flask import jsonify, request
from werkzeug.exceptions import BadRequest, NotFound, Conflict

from . import api
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .rounds import is_round_complete, end_round, get_current_round
from ..auth import with_jurisdiction_access
from ..util.jsonschema import JSONDict, validate

OFFLINE_RESULTS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^.*$": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "integer", "minimum": 0}},
        }
    },
}


def validate_offline_results(
    election: Election, jurisdiction: Jurisdiction, round: Round, results: JSONDict
):
    if election.online:
        raise Conflict("Cannot record offline results for online audit.")

    current_round = get_current_round(election)
    if not current_round or round.id != current_round.id:
        raise Conflict(f"Round {round.round_num} is not the current round")

    num_audit_boards = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).count()
    if num_audit_boards == 0:
        raise Conflict("Must set up audit boards before recording results")

    validate(results, OFFLINE_RESULTS_SCHEMA)

    contest_ids = {c.id for c in jurisdiction.contests}
    if set(results.keys()) != contest_ids:
        raise BadRequest("Invalid contest ids")

    choices_by_contest = dict(
        ContestChoice.query.filter(ContestChoice.contest_id.in_(contest_ids))
        .group_by(ContestChoice.contest_id)
        .values(ContestChoice.contest_id, func.array_agg(ContestChoice.id))
    )
    for contest_id, results_by_choice in results.items():
        if set(results_by_choice.keys()) != set(choices_by_contest[contest_id]):
            raise BadRequest(f"Invalid choice ids for contest {contest_id}")

    ballot_draws_by_contest = dict(
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .join(SampledBallotDraw)
        .filter_by(round_id=current_round.id)
        .group_by(SampledBallotDraw.contest_id)
        .values(SampledBallotDraw.contest_id, func.count())
    )
    ballots_sampled = (
        SampledBallot.query.join(Batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .count()
    )
    for contest in jurisdiction.contests:
        num_ballots = (
            ballot_draws_by_contest.get(contest.id, 0)
            if contest.is_targeted
            else ballots_sampled
        )
        total_results = sum(results[contest.id].values())
        allowed_results = num_ballots * contest.votes_allowed
        if total_results > allowed_results:
            raise BadRequest(
                f"Total results for contest {contest.name} should not exceed"
                f" {allowed_results} - the number of sampled ballots ({num_ballots})"
                f" times the number of votes allowed ({contest.votes_allowed}).",
            )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/results",
    methods=["PUT"],
)
@with_jurisdiction_access
def record_offline_results(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round_id: str,
):
    round = Round.query.filter_by(id=round_id, election_id=election.id).first()
    if round is None:
        raise NotFound()

    results = request.get_json()
    validate_offline_results(election, jurisdiction, round, results)

    for round_contest in round.round_contests:
        JurisdictionResult.query.filter_by(
            round_id=round.id,
            contest_id=round_contest.contest_id,
            jurisdiction_id=jurisdiction.id,
        ).delete()
        jurisdiction_results = [
            JurisdictionResult(
                round_id=round.id,
                contest_id=round_contest.contest_id,
                jurisdiction_id=jurisdiction.id,
                contest_choice_id=choice_id,
                result=result,
            )
            for choice_id, result in results[round_contest.contest_id].items()
        ]
        db_session.add_all(jurisdiction_results)

    if is_round_complete(election, round):
        end_round(election, round)

    db_session.commit()

    return jsonify(status="ok")


def serialize_results(round: Round, results: List[JurisdictionResult]) -> JSONDict:
    def result_for_choice(contest_id: str, choice_id: str) -> Optional[int]:
        return next(
            (
                r.result
                for r in results
                if r.contest_id == contest_id and r.contest_choice_id == choice_id
            ),
            None,
        )

    return {
        round_contest.contest_id: {
            choice.id: result_for_choice(round_contest.contest_id, choice.id)
            for choice in round_contest.contest.choices
        }
        for round_contest in round.round_contests
    }


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/results",
    methods=["GET"],
)
@with_jurisdiction_access
def get_offline_results(
    election: Election,
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
    round_id: str,
):
    round = Round.query.filter_by(id=round_id, election_id=election.id).first()
    if round is None:
        raise NotFound()

    results = JurisdictionResult.query.filter_by(
        jurisdiction_id=jurisdiction.id, round_id=round.id
    ).all()
    return jsonify(serialize_results(round, results))
