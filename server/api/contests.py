import typing
from typing import List
from flask import request, jsonify
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..auth import restrict_access, UserType
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import validate, JSONDict
from .cvrs import hybrid_contest_choice_vote_counts, set_contest_metadata_from_cvrs
from .ballot_manifest import set_total_ballots_from_manifests


CONTEST_CHOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "numVotes": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
    "required": ["id", "name", "numVotes"],
}

CONTEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "isTargeted": {"type": "boolean"},
        "choices": {"type": "array", "items": CONTEST_CHOICE_SCHEMA},
        "numWinners": {"type": "integer", "minimum": 1},
        "votesAllowed": {"type": "integer", "minimum": 1},
        "jurisdictionIds": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
    "required": [
        "id",
        "name",
        "isTargeted",
        "choices",
        "numWinners",
        "votesAllowed",
        "jurisdictionIds",
    ],
}

# In ballot polling audits, the AA also enters the total ballots cast.
# In all other audit types, we compute this value from the manifests.
BALLOT_POLLING_CONTEST_SCHEMA = {
    "type": "object",
    "properties": {
        **typing.cast(dict, CONTEST_SCHEMA["properties"]),
        "totalBallotsCast": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
    "required": typing.cast(list, CONTEST_SCHEMA["required"]) + ["totalBallotsCast"],
}

# In ballot comparison audits, the AA selects contests from the standardized
# contests file, so we create contests without choices, totalBallotsCast, and
# votesAllowed. We later populate these fields using the metadata in the CVRs
# that the jurisdictions provide.
BALLOT_COMPARISON_CONTEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "isTargeted": {"type": "boolean"},
        "numWinners": {"type": "integer", "minimum": 1},
        "jurisdictionIds": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
    "required": ["id", "name", "isTargeted", "numWinners", "jurisdictionIds"],
}


def serialize_contest(contest: Contest) -> JSONDict:
    choices = [
        {"id": choice.id, "name": choice.name, "numVotes": choice.num_votes,}
        for choice in contest.choices
    ]
    if contest.election.audit_type == AuditType.HYBRID:
        vote_counts = hybrid_contest_choice_vote_counts(contest)
        for choice in choices:
            choice["numVotesCvr"] = vote_counts and vote_counts[str(choice["id"])].cvr
            choice["numVotesNonCvr"] = (
                vote_counts and vote_counts[str(choice["id"])].non_cvr
            )

    return {
        "id": contest.id,
        "name": contest.name,
        "isTargeted": contest.is_targeted,
        "choices": choices,
        "totalBallotsCast": contest.total_ballots_cast,
        "numWinners": contest.num_winners,
        "votesAllowed": contest.votes_allowed,
        "jurisdictionIds": [j.id for j in contest.jurisdictions],
    }


def deserialize_contest_choice(
    contest_choice: JSONDict, contest_id: str
) -> ContestChoice:
    return ContestChoice(
        id=contest_choice["id"],
        contest_id=contest_id,
        name=contest_choice["name"],
        num_votes=contest_choice["numVotes"],
    )


def deserialize_contest(contest: JSONDict, election_id: str) -> Contest:
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .filter(Jurisdiction.id.in_(contest["jurisdictionIds"]))
        .all()
    )
    choices = [
        deserialize_contest_choice(choice, contest["id"])
        for choice in contest.get("choices", [])
    ]
    return Contest(
        election_id=election_id,
        id=contest["id"],
        name=contest["name"],
        is_targeted=contest["isTargeted"],
        choices=choices,
        total_ballots_cast=contest.get("totalBallotsCast", None),
        num_winners=contest.get("numWinners", None),
        votes_allowed=contest.get("votesAllowed", None),
        jurisdictions=jurisdictions,
    )


# Raises if invalid
def validate_contests(contests: List[JSONDict], election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update contests after audit has started.")

    validate(
        contests,
        {
            "type": "array",
            "items": {
                AuditType.BALLOT_POLLING: BALLOT_POLLING_CONTEST_SCHEMA,
                AuditType.BATCH_COMPARISON: CONTEST_SCHEMA,
                AuditType.BALLOT_COMPARISON: BALLOT_COMPARISON_CONTEST_SCHEMA,
                AuditType.HYBRID: CONTEST_SCHEMA,
            }[AuditType(election.audit_type)],
        },
    )

    contest_jurisdiction_ids = set(
        id for contest in contests for id in contest["jurisdictionIds"]
    )
    if Jurisdiction.query.filter(
        Jurisdiction.id.in_(contest_jurisdiction_ids)
    ).count() < len(contest_jurisdiction_ids):
        raise BadRequest("Invalid jurisdiction ids")

    if not any(contest["isTargeted"] for contest in contests):
        raise BadRequest("Must have at least one targeted contest")

    if election.audit_type == AuditType.BATCH_COMPARISON and len(contests) > 1:
        raise BadRequest("Batch comparison audits may only have one contest.")

    # TODO some validation for Hybrid?
    if election.audit_type == AuditType.BALLOT_POLLING:
        for contest in contests:
            total_votes = sum(c["numVotes"] for c in contest["choices"])
            total_allowed_votes = contest["totalBallotsCast"] * contest["votesAllowed"]
            if total_votes > total_allowed_votes:
                raise BadRequest(
                    f"Too many votes cast in contest: {contest['name']}"
                    f" ({total_votes} votes, {total_allowed_votes} allowed)"
                )


@api.route("/election/<election_id>/contest", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def create_or_update_all_contests(election: Election):
    json_contests = request.get_json()
    validate_contests(json_contests, election)

    Contest.query.filter_by(election_id=election.id).delete()

    contests = [
        deserialize_contest(json_contest, election.id) for json_contest in json_contests
    ]
    db_session.add_all(contests)

    if election.audit_type != AuditType.BALLOT_POLLING:
        for contest in contests:
            set_total_ballots_from_manifests(contest)

    if election.audit_type == AuditType.BALLOT_COMPARISON:
        for contest in contests:
            set_contest_metadata_from_cvrs(contest)

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/contest", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def list_contests(election: Election):
    json_contests = [serialize_contest(c) for c in election.contests]
    return jsonify({"contests": json_contests})


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/contest", methods=["GET"]
)
@restrict_access([UserType.JURISDICTION_ADMIN])
def list_jurisdictions_contests(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    json_contests = [serialize_contest(c) for c in jurisdiction.contests]
    return jsonify({"contests": json_contests})


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/contest",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_BOARD])
def list_audit_board_contests(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
    round: Round,  # pylint: disable=unused-argument
    audit_board: AuditBoard,  # pylint: disable=unused-argument
):
    json_contests = [serialize_contest(c) for c in jurisdiction.contests]
    return jsonify({"contests": json_contests})


# { jurisdiction_id: { contest_name: cvr_contest_name | null }}
CONTEST_NAME_STANDARDIZATIONS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^.*$": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]
                }
            },
        },
    },
}


@api.route("/election/<election_id>/contest/standardizations", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def put_contest_name_standardizations(election: Election):
    if election.audit_type not in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        raise Conflict("Cannot standardize contest names for this audit type")
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot standardize contest names after the audit has started.")

    standardizations = request.get_json()
    validate(standardizations, CONTEST_NAME_STANDARDIZATIONS_SCHEMA)

    for jurisdiction in election.jurisdictions:
        jurisdiction.contest_name_standardizations = standardizations.get(
            jurisdiction.id
        )

    for contest in election.contests:
        set_contest_metadata_from_cvrs(contest)

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/contest/standardizations", methods=["GET"])
@restrict_access([UserType.AUDIT_ADMIN])
def get_contest_name_standardizations(election: Election):
    def standardizations(jurisdiction):
        if jurisdiction.cvr_contests_metadata is None:
            return None
        contests_needing_standardization = [
            contest
            for contest in jurisdiction.contests
            if contest.name not in jurisdiction.cvr_contests_metadata
        ]
        # Since CVR contests could have changed since these mappings were
        # created, filter out any outdated standardizations.
        valid_standardizations = {
            contest_name: cvr_contest_name
            for contest_name, cvr_contest_name in (
                jurisdiction.contest_name_standardizations or {}
            ).items()
            if cvr_contest_name in jurisdiction.cvr_contests_metadata
        }
        return {
            contest.name: valid_standardizations.get(contest.name)
            for contest in contests_needing_standardization
        }

    standardizations_by_jurisdiction = {
        jurisdiction: standardizations(jurisdiction)
        for jurisdiction in election.jurisdictions
    }

    return jsonify(
        standardizations={
            jurisdiction.id: jurisdiction_standardizations
            for jurisdiction, jurisdiction_standardizations in standardizations_by_jurisdiction.items()
            if jurisdiction_standardizations
        },
        cvrContestNames={
            jurisdiction.id: list(
                typing.cast(dict, jurisdiction.cvr_contests_metadata).keys()
            )
            for jurisdiction, jurisdiction_standardizations in standardizations_by_jurisdiction.items()
            if jurisdiction_standardizations
        },
    )
