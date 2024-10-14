import typing
from typing import Dict, List, Optional
from collections import defaultdict
from flask import request, jsonify, session
from werkzeug.exceptions import BadRequest, Conflict

from . import api
from ..auth import restrict_access, UserType, get_loggedin_user, get_support_user
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.jsonschema import validate, JSONDict
from . import cvrs  # pylint: disable=cyclic-import
from . import ballot_manifest  # pylint: disable=cyclic-import
from . import batch_tallies  # pylint: disable=cyclic-import
from ..util.get_json import safe_get_json_dict, safe_get_json_list


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
        "cvrChoiceNameConsistencyError": {
            "type": "object",
            "properties": {
                "anomalousCvrChoiceNamesByJurisdiction": {
                    "type": "object",
                    "patternProperties": {
                        "^.*$": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "cvrChoiceNamesInJurisdictionWithMostCvrChoices": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "jurisdictionIdWithMostCvrChoices": {"type": "string"},
            },
            "additionalProperties": False,
            "required": [
                "anomalousCvrChoiceNamesByJurisdiction",
                "cvrChoiceNamesInJurisdictionWithMostCvrChoices",
                "jurisdictionIdWithMostCvrChoices",
            ],
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
        {
            "id": choice.id,
            "name": choice.name,
            "numVotes": choice.num_votes,
        }
        for choice in contest.choices
    ]
    if contest.election.audit_type == AuditType.HYBRID:
        vote_counts = cvrs.hybrid_contest_choice_vote_counts(contest)
        for choice in choices:
            choice["numVotesCvr"] = vote_counts and vote_counts[str(choice["id"])].cvr
            choice["numVotesNonCvr"] = (
                vote_counts and vote_counts[str(choice["id"])].non_cvr
            )

    serialized_contest = {
        "id": contest.id,
        "name": contest.name,
        "isTargeted": contest.is_targeted,
        "choices": choices,
        "totalBallotsCast": contest.total_ballots_cast,
        "numWinners": contest.num_winners,
        "votesAllowed": contest.votes_allowed,
        "jurisdictionIds": [j.id for j in contest.jurisdictions],
    }

    # Validate CVR choice names across jurisdictions in ballot comparison audits. Load error
    # details, if any, onto the contest object.
    if contest.election.audit_type == AuditType.BALLOT_COMPARISON:
        cvr_choice_names_by_jurisdiction: Dict[str, List[str]] = {}
        jurisdiction_id_with_most_cvr_choices: Optional[str] = None

        for jurisdiction in contest.jurisdictions:
            metadata = cvrs.cvr_contests_metadata(jurisdiction)
            if metadata is not None and contest.name in metadata:
                cvr_choice_names = list(metadata[contest.name]["choices"].keys())
                cvr_choice_names.sort()
                cvr_choice_names_by_jurisdiction[jurisdiction.id] = cvr_choice_names

                if jurisdiction_id_with_most_cvr_choices is None or len(
                    cvr_choice_names
                ) > len(
                    cvr_choice_names_by_jurisdiction[
                        jurisdiction_id_with_most_cvr_choices
                    ]
                ):
                    jurisdiction_id_with_most_cvr_choices = jurisdiction.id

        if len(cvr_choice_names_by_jurisdiction) > 1:
            assert jurisdiction_id_with_most_cvr_choices is not None

            anomalous_cvr_choice_names_by_jurisdiction = {}
            for (
                jurisdiction_id,
                cvr_choice_names,
            ) in cvr_choice_names_by_jurisdiction.items():
                if jurisdiction_id == jurisdiction_id_with_most_cvr_choices:
                    continue

                anomalous_cvr_choice_names = list(
                    set(cvr_choice_names)
                    - set(
                        cvr_choice_names_by_jurisdiction[
                            jurisdiction_id_with_most_cvr_choices
                        ]
                    )
                )
                anomalous_cvr_choice_names.sort()

                if len(anomalous_cvr_choice_names) > 0:
                    anomalous_cvr_choice_names_by_jurisdiction[jurisdiction_id] = (
                        anomalous_cvr_choice_names
                    )

            if len(anomalous_cvr_choice_names_by_jurisdiction) > 0:
                serialized_contest["cvrChoiceNameConsistencyError"] = {
                    "anomalousCvrChoiceNamesByJurisdiction": anomalous_cvr_choice_names_by_jurisdiction,
                    "cvrChoiceNamesInJurisdictionWithMostCvrChoices": cvr_choice_names_by_jurisdiction[
                        jurisdiction_id_with_most_cvr_choices
                    ],
                    "jurisdictionIdWithMostCvrChoices": jurisdiction_id_with_most_cvr_choices,
                }

    return serialized_contest


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


# In various audit types, we set different pieces of contest metadata from
# different underlying data sources (e.g. manifest or CVR files). Whenever a
# contest changes or when those data sources change, we need to recompute the
# metadata.
def set_contest_metadata(election: Election):
    for contest in election.contests:
        if election.audit_type != AuditType.BALLOT_POLLING:
            ballot_manifest.set_total_ballots_from_manifests(contest)
        if election.audit_type == AuditType.BALLOT_COMPARISON:
            cvrs.set_contest_metadata_from_cvrs(contest)


@api.route("/election/<election_id>/contest", methods=["PUT"])
@restrict_access([UserType.AUDIT_ADMIN])
def create_or_update_all_contests(election: Election):
    json_contests = safe_get_json_list(request)
    validate_contests(json_contests, election)

    Contest.query.filter_by(election_id=election.id).delete()
    election.contests = [
        deserialize_contest(json_contest, election.id) for json_contest in json_contests
    ]

    set_contest_metadata(election)

    if election.audit_type == AuditType.BATCH_COMPARISON:
        user = get_loggedin_user(session)
        assert user[0] is not None
        for jurisdiction in election.jurisdictions:
            batch_tallies.reprocess_batch_tallies_file_if_uploaded(
                jurisdiction,
                user,
                get_support_user(session),
            )

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
@restrict_access(
    [UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN, UserType.TALLY_ENTRY]
)
def list_jurisdictions_contests(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
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


# { jurisdiction_id: { contest_name: cvr_contest_name | null } }
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

# { jurisdiction_id: { contest_id: { cvr_choice_name: choice_name | null } } }
CONTEST_CHOICE_NAME_STANDARDIZATIONS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^.*$": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "patternProperties": {
                        "^.*$": {
                            "anyOf": [
                                {"type": "string", "minLength": 1},
                                {"type": "null"},
                            ]
                        }
                    },
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

    standardizations = safe_get_json_dict(request)
    validate(standardizations, CONTEST_NAME_STANDARDIZATIONS_SCHEMA)

    for jurisdiction in election.jurisdictions:
        jurisdiction.contest_name_standardizations = standardizations.get(
            jurisdiction.id
        )

    set_contest_metadata(election)

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


@api.route(
    "/election/<election_id>/contest/choice-name-standardizations",
    methods=["PUT"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def put_contest_choice_name_standardizations(election: Election):  # pragma: no cover
    if election.audit_type not in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
        raise Conflict("Cannot standardize contest choice names for this audit type.")
    if len(list(election.rounds)) > 0:
        raise Conflict(
            "Cannot standardize contest choice names after the audit has started."
        )

    standardizations = safe_get_json_dict(request)
    validate(standardizations, CONTEST_CHOICE_NAME_STANDARDIZATIONS_SCHEMA)

    for jurisdiction in election.jurisdictions:
        jurisdiction.contest_choice_name_standardizations = standardizations.get(
            jurisdiction.id, None
        )

    set_contest_metadata(election)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/contest/choice-name-standardizations",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def get_contest_choice_name_standardizations(election: Election):  # pragma: no cover
    def get_standardizations_for_jurisdiction_and_contest(jurisdiction, contest):
        # Get metadata with contest name standardizations applied but not contest choice name
        # standardizations applied
        metadata = cvrs.cvr_contests_metadata(
            jurisdiction, should_standardize_contest_choice_names=False
        )
        cvr_choice_names = list(
            (metadata or {}).get(contest.name, {}).get("choices", {}).keys()
        )

        standardized_contests = (
            typing.cast(Optional[List[Dict]], election.standardized_contests) or []
        )
        standardized_contest_choice_names = next(
            (
                standardized_contest.get("choiceNames", None)
                for standardized_contest in standardized_contests
                if standardized_contest["name"] == contest.name
            ),
            None,
        )

        raw_standardizations = (
            typing.cast(
                Optional[Dict[str, Dict[str, Optional[str]]]],
                jurisdiction.contest_choice_name_standardizations,
            )
            or {}
        ).get(contest.id, {})

        standardizations = {
            cvr_choice_name: raw_standardizations.get(cvr_choice_name, None)
            for cvr_choice_name in cvr_choice_names
            # Include as keys all CVR choice names requiring standardization and no other CVR
            # choice names. The frontend uses the presence of keys to determine whether
            # standardization is needed/outstanding.
            if standardized_contest_choice_names is not None
            and cvr_choice_name not in standardized_contest_choice_names
        }
        return standardizations

    all_standardizations: Dict[str, Dict[str, Dict[str, Optional[str]]]] = defaultdict(
        dict
    )
    for jurisdiction in election.jurisdictions:
        for contest in election.contests:
            standardizations = get_standardizations_for_jurisdiction_and_contest(
                jurisdiction, contest
            )
            if standardizations:
                all_standardizations[jurisdiction.id][contest.id] = standardizations

    return jsonify(standardizations=all_standardizations)
