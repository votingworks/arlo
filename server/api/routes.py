import datetime, csv, io, json, uuid
from typing import Dict, List, Tuple

from flask import jsonify, request
from werkzeug.exceptions import NotFound, Forbidden, Conflict

from xkcdpass import xkcd_password as xp

from sqlalchemy.orm.session import Session


from . import api
from ..auth import with_election_access, require_audit_admin_for_organization
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from .ballots import (
    ballot_retrieval_list,
    serialize_interpretation,
    deserialize_interpretation,
)
from .ballot_manifest import (
    save_ballot_manifest_file,
    clear_ballot_manifest_file,
)
from .audit_boards import serialize_members
from .sample_sizes import cumulative_contest_results
from ..audit_math import bravo, sampler_contest, sampler
from ..util.binpacking import BalancedBucketList, Bucket
from ..util.csv_parse import decode_csv_file
from ..util.isoformat import isoformat
from ..util.jsonschema import validate, JSONDict
from ..util.process_file import serialize_file, serialize_file_processing
from ..util.csv_download import election_timestamp_name, csv_response

AUDIT_BOARD_MEMBER_COUNT = 2
WORDS = xp.generate_wordlist(wordfile=xp.locate_wordfile())


def create_organization(name=""):
    org = Organization(id=str(uuid.uuid4()), name=name)
    db_session.add(org)
    db_session.commit()
    return org


def get_election(election_id):
    return Election.query.filter_by(id=election_id).one()


def compute_sample_sizes(round_contest):
    the_round = round_contest.round
    election = the_round.election

    for contest in election.contests:
        raw_sample_size_options = bravo.get_sample_size(
            election.risk_limit / 100,
            sampler_contest.from_db_contest(contest),
            cumulative_contest_results(contest),
        )

        sample_size_options = list(raw_sample_size_options.values())
        sample_size_backup = raw_sample_size_options["asn"]["size"]
        sample_size_90 = (
            raw_sample_size_options["0.9"]["size"]
            if "0.9" in raw_sample_size_options
            else None
        )

        round_contest.sample_size_options = json.dumps(sample_size_options)

        # if we are in multi-winner, there is no sample_size_90 so fix it
        if not sample_size_90:
            sample_size_90 = sample_size_backup

        # for later rounds, we always pick 90%
        if round_contest.round.round_num > 1:
            round_contest.sample_size = sample_size_90
            sample_ballots(db_session, election, the_round)

    db_session.commit()


def setup_next_round(election):
    if len(election.contests) > 1:
        raise Exception("only supports one contest for now")  # pragma: no cover

    rounds = Round.query.filter_by(election_id=election.id).order_by("round_num").all()

    print("adding round {:d} for election {:s}".format(len(rounds) + 1, election.id))
    round = Round(
        id=str(uuid.uuid4()), election_id=election.id, round_num=len(rounds) + 1,
    )

    db_session.add(round)

    # assume just one contest for now
    contest = election.contests[0]
    round_contest = RoundContest(round_id=round.id, contest_id=contest.id)

    db_session.add(round_contest)


def check_round(election, jurisdiction_id, round_id):
    assert Jurisdiction.query.get(jurisdiction_id)
    round = Round.query.get(round_id)

    # assume one contest
    round_contest = round.round_contests[0]
    contest = next(c for c in election.contests if c.id == round_contest.contest_id)

    risk, is_complete = bravo.compute_risk(
        election.risk_limit / 100,
        sampler_contest.from_db_contest(contest),
        cumulative_contest_results(contest),
    )

    round.ended_at = datetime.datetime.utcnow()
    # TODO this is a hack, should we report pairwise p-values?
    round_contest.end_p_value = max(risk.values())
    round_contest.is_complete = is_complete

    db_session.commit()

    return is_complete


def sample_ballots(session: Session, election: Election, round: Round):
    # assume only one contest
    round_contest = list(round.round_contests)[0]
    jurisdiction = list(election.jurisdictions)[0]

    num_sampled = (
        session.query(SampledBallotDraw)
        .join(SampledBallot)
        .join(SampledBallot.batch)
        .filter_by(jurisdiction_id=jurisdiction.id)
        .count()
    )
    if not num_sampled:
        num_sampled = 0

    if not round_contest.sample_size:  # Shouldn't happen, need this for typechecking
        raise Exception("Sample size not set")
    chosen_sample_size: int = round_contest.sample_size

    # the sampler needs to have the same inputs given the same manifest
    # so we use the batch name, rather than the batch id
    # (because the batch ID is an internally generated uuid
    #  that changes from one run to the next.)
    manifest = {}
    batch_id_from_name = {}
    for batch in jurisdiction.batches:
        manifest[batch.name] = batch.num_ballots
        batch_id_from_name[batch.name] = batch.id

    sample = sampler.draw_sample(
        str(election.random_seed),
        manifest,
        chosen_sample_size,
        num_sampled=num_sampled,
    )

    audit_boards = list(jurisdiction.audit_boards)

    batch_sizes: Dict[str, int] = {}
    batches_to_ballots: Dict[str, List[Tuple[int, str, int]]] = {}
    # Build batch - batch_size map
    for (ticket_number, (batch_name, ballot_position), sample_number) in sample:
        if batch_name in batch_sizes:
            if (
                sample_number == 1
            ):  # if we've already seen it, it doesn't affect batch size
                batch_sizes[batch_name] += 1
            batches_to_ballots[batch_name].append(
                (ballot_position, ticket_number, sample_number)
            )
        else:
            batch_sizes[batch_name] = 1
            batches_to_ballots[batch_name] = [
                (ballot_position, ticket_number, sample_number)
            ]

    # Create the buckets and initially assign batches
    buckets = [Bucket(str(audit_board.name)) for audit_board in audit_boards]
    for i, batch_name in enumerate(batch_sizes):
        buckets[i % len(audit_boards)].add_batch(batch_name, batch_sizes[batch_name])

    # Now assign batchest fairly
    bucket_list = BalancedBucketList(buckets)

    # read audit board and batch info out
    for audit_board_num, bucket in enumerate(bucket_list.buckets):
        audit_board = audit_boards[audit_board_num]
        for batch_name in bucket.batches:

            for (ballot_position, ticket_number, sample_number) in batches_to_ballots[
                batch_name
            ]:
                batch_id = batch_id_from_name[batch_name]

                if sample_number == 1:
                    sampled_ballot = SampledBallot(
                        id=str(uuid.uuid4()),
                        batch_id=batch_id,
                        ballot_position=ballot_position,
                        audit_board_id=audit_board.id,
                        status=BallotStatus.NOT_AUDITED,
                    )
                    session.add(sampled_ballot)
                else:
                    sampled_ballot = SampledBallot.query.filter_by(
                        batch_id=batch_id, ballot_position=ballot_position,
                    ).one()

                sampled_ballot_draw = SampledBallotDraw(
                    ballot_id=sampled_ballot.id,
                    round_id=round.id,
                    contest_id=round_contest.contest_id,
                    ticket_number=ticket_number,
                )

                session.add(sampled_ballot_draw)

    session.commit()


ELECTION_NEW_SCHEMA = {
    "type": "object",
    "properties": {
        "auditName": {"type": "string"},
        "auditType": {
            "type": "string",
            "enum": [audit_type.value for audit_type in AuditType],
        },
        "organizationId": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "isMultiJurisdiction": {"type": "boolean"},
    },
    "required": ["auditName", "isMultiJurisdiction"],
    "additionalProperties": False,
}


def validate_new_election(election: JSONDict, organization_id: str):
    validate(election, ELECTION_NEW_SCHEMA)
    if (
        organization_id
        and Election.query.filter_by(
            audit_name=election["auditName"], organization_id=organization_id
        ).first()
    ):
        raise Conflict(
            f"An audit with name '{election['auditName']}' already exists within your organization"
        )


@api.route("/election/new", methods=["POST"])
def election_new():
    election = request.get_json()

    organization_id = election.get("organizationId", None)
    require_audit_admin_for_organization(organization_id)

    validate_new_election(election, organization_id)

    election = Election(
        id=str(uuid.uuid4()),
        audit_name=election["auditName"],
        audit_type=election["auditType"],
        organization_id=organization_id,
        is_multi_jurisdiction=election["isMultiJurisdiction"],
    )
    db_session.add(election)

    db_session.commit()

    return jsonify(electionId=election.id)


@api.route("/election/<election_id>/jurisdiction/file", methods=["GET"])
@with_election_access
def get_jurisdictions_file(election: Election):
    jurisdictions_file = election.jurisdictions_file

    if jurisdictions_file:
        return jsonify(
            file=serialize_file(jurisdictions_file),
            processing=serialize_file_processing(jurisdictions_file),
        )
    return jsonify(file=None, processing=None)


@api.route("/election/<election_id>/jurisdiction/file/csv", methods=["GET"])
@with_election_access
def download_jurisdictions_file(election: Election):
    if not election.jurisdictions_file:
        return NotFound()

    return csv_response(
        election.jurisdictions_file.contents, election.jurisdictions_file.name
    )


JURISDICTION_NAME = "Jurisdiction"
ADMIN_EMAIL = "Admin Email"


@api.route("/election/<election_id>/jurisdiction/file", methods=["PUT"])
@with_election_access
def update_jurisdictions_file(election: Election):
    if len(list(election.rounds)) > 0:
        raise Conflict("Cannot update jurisdictions after audit has started.")

    if "jurisdictions" not in request.files:
        return (
            jsonify(
                errors=[
                    {
                        "message": 'Expected file parameter "jurisdictions" was missing',
                        "errorType": "MissingFile",
                    }
                ]
            ),
            400,
        )

    jurisdictions_file = request.files["jurisdictions"]
    jurisdictions_file_string = decode_csv_file(jurisdictions_file.read())

    old_jurisdictions_file = election.jurisdictions_file
    election.jurisdictions_file = File(
        id=str(uuid.uuid4()),
        name=jurisdictions_file.filename,
        contents=jurisdictions_file_string,
        uploaded_at=datetime.datetime.utcnow(),
    )

    jurisdictions_csv = csv.DictReader(io.StringIO(jurisdictions_file_string))

    missing_fields = [
        field
        for field in [JURISDICTION_NAME, ADMIN_EMAIL]
        if field not in (jurisdictions_csv.fieldnames or [])
    ]

    if missing_fields:
        return (
            jsonify(
                errors=[
                    {
                        "message": f'Missing required CSV field "{field}"',
                        "errorType": "MissingRequiredCsvField",
                        "fieldName": field,
                    }
                    for field in missing_fields
                ]
            ),
            400,
        )

    if old_jurisdictions_file:
        db_session.delete(old_jurisdictions_file)
    db_session.add(election)
    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/audit/status", methods=["GET"])
@with_election_access
def audit_status(election):
    return jsonify(
        organizationId=election.organization_id,
        name=election.election_name,
        online=election.online,
        frozenAt=isoformat(election.frozen_at),
        riskLimit=election.risk_limit,
        randomSeed=election.random_seed,
        isMultiJurisdiction=election.is_multi_jurisdiction,
        contests=[
            {
                "id": contest.id,
                "name": contest.name,
                "isTargeted": contest.is_targeted,
                "choices": [
                    {"id": choice.id, "name": choice.name, "numVotes": choice.num_votes}
                    for choice in contest.choices
                ],
                "totalBallotsCast": contest.total_ballots_cast,
                "numWinners": contest.num_winners,
                "votesAllowed": contest.votes_allowed,
            }
            for contest in election.contests
        ],
        jurisdictions=[
            {
                "id": j.id,
                "name": j.name,
                "contests": [c.id for c in j.contests],
                "auditBoards": [
                    {
                        "id": audit_board.id,
                        "name": audit_board.name,
                        "members": serialize_members(audit_board),
                        "passphrase": audit_board.passphrase,
                    }
                    for audit_board in j.audit_boards
                ],
                "ballotManifest": {
                    "file": serialize_file(j.manifest_file)
                    if j.manifest_file
                    else None,
                    "processing": serialize_file_processing(j.manifest_file)
                    if j.manifest_file
                    else None,
                    "numBallots": j.manifest_num_ballots,
                    "numBatches": j.manifest_num_batches,
                    # Deprecated fields.
                    "filename": j.manifest_file.name if j.manifest_file else None,
                    "uploadedAt": isoformat(j.manifest_file.uploaded_at)
                    if j.manifest_file
                    else None,
                },
                "batches": [
                    {
                        "id": batch.id,
                        "name": batch.name,
                        "numBallots": batch.num_ballots,
                        "storageLocation": batch.storage_location,
                        "tabulator": batch.tabulator,
                    }
                    for batch in j.batches
                ],
            }
            for j in election.jurisdictions
        ],
        rounds=[
            {
                "id": round.id,
                "startedAt": isoformat(round.created_at),
                "endedAt": isoformat(round.ended_at),
                "contests": [
                    {
                        "id": round_contest.contest_id,
                        "endMeasurements": {
                            "pvalue": round_contest.end_p_value,
                            "isComplete": round_contest.is_complete,
                        },
                        "results": {
                            result.contest_choice_id: result.result
                            for result in round_contest.results
                        },
                        "sampleSizeOptions": json.loads(
                            round_contest.sample_size_options or "null"
                        ),
                        "sampleSize": round_contest.sample_size,
                    }
                    # pylint: disable=no-member
                    # (seems like a pylint bug)
                    for round_contest in round.round_contests
                ],
            }
            for round in election.rounds
        ],
    )


@api.route("/election/<election_id>/audit/basic", methods=["POST"])
@with_election_access
def audit_basic_update(election):
    info = request.get_json()
    election.election_name = info["name"]
    election.risk_limit = info["riskLimit"]
    election.random_seed = info["randomSeed"]
    election.online = info["online"]

    errors = []
    Contest.query.filter_by(election_id=election.id).delete()

    for contest in info["contests"]:
        total_allowed_votes_in_contest = (
            contest["totalBallotsCast"] * contest["votesAllowed"]
        )

        contest_obj = Contest(
            election_id=election.id,
            id=contest["id"],
            name=contest["name"],
            is_targeted=contest.get("isTargeted", True),
            total_ballots_cast=contest["totalBallotsCast"],
            num_winners=contest["numWinners"],
            votes_allowed=contest["votesAllowed"],
        )
        db_session.add(contest_obj)

        total_votes_in_all_choices = 0

        for choice in contest["choices"]:
            total_votes_in_all_choices += choice["numVotes"]

            choice_obj = ContestChoice(
                id=choice["id"],
                contest_id=contest_obj.id,
                name=choice["name"],
                num_votes=choice["numVotes"],
            )
            db_session.add(choice_obj)

        if total_votes_in_all_choices > total_allowed_votes_in_contest:
            errors.append(
                {
                    "message": f'Too many votes cast in contest: {contest["name"]} ({total_votes_in_all_choices} votes, {total_allowed_votes_in_contest} allowed)',
                    "errorType": "TooManyVotes",
                }
            )

    if errors:
        db_session.rollback()
        return jsonify(errors=errors), 400

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/audit/sample-size", methods=["POST"])
@with_election_access
def samplesize_set(election):
    # only works if there's only one round
    rounds = election.rounds
    if len(rounds) > 1:
        return jsonify(status="bad")  # pragma: no cover

    rounds[0].round_contests[0].sample_size = int(request.get_json()["size"])
    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/audit/jurisdictions", methods=["POST"])
@with_election_access
def jurisdictions_set(election):
    jurisdictions = request.get_json()["jurisdictions"]

    Jurisdiction.query.filter_by(election_id=election.id).delete()

    for jurisdiction in jurisdictions:
        contests = (
            Contest.query.filter_by(election_id=election.id)
            .filter(Contest.id.in_(jurisdiction["contests"]))
            .all()
        )
        jurisdiction_obj = Jurisdiction(
            election_id=election.id,
            id=jurisdiction["id"],
            name=jurisdiction["name"],
            contests=contests,
        )
        db_session.add(jurisdiction_obj)

        for audit_board in jurisdiction["auditBoards"]:
            audit_board_obj = AuditBoard(
                id=audit_board["id"],
                name=audit_board["name"],
                jurisdiction_id=jurisdiction_obj.id,
                passphrase=xp.generate_xkcdpassword(WORDS, numwords=4, delimiter="-"),
            )
            db_session.add(audit_board_obj)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/manifest",
    methods=["DELETE", "PUT"],
)
@with_election_access
def jurisdiction_manifest(election, jurisdiction_id):
    jurisdiction = Jurisdiction.query.filter_by(
        election_id=election.id, id=jurisdiction_id
    ).first()

    if not jurisdiction:
        raise NotFound()
    if election.is_multi_jurisdiction:
        raise Forbidden()

    if request.method == "DELETE":
        clear_ballot_manifest_file(jurisdiction)
    else:
        save_ballot_manifest_file(request.files["manifest"], jurisdiction)

    db_session.commit()
    return jsonify(status="ok")


@api.route("/election/<election_id>/audit/freeze", methods=["POST"])
@with_election_access
def audit_launch(election):
    # don't freeze an already frozen election
    if election.frozen_at:
        return jsonify(status="ok")

    election.frozen_at = datetime.datetime.utcnow()
    db_session.add(election)

    # prepare the first round, including sample sizes
    setup_next_round(election)

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>",
    methods=["GET"],
)
@with_election_access
def audit_board(election, jurisdiction_id, audit_board_id):
    audit_boards = (
        AuditBoard.query.filter_by(id=audit_board_id)
        .join(AuditBoard.jurisdiction)
        .filter_by(id=jurisdiction_id, election_id=election.id)
        .all()
    )

    if not audit_boards:
        return f"no audit board found with id={audit_board_id}", 404

    if len(audit_boards) > 1:
        return f"found too many audit boards with id={audit_board_id}", 400

    audit_board = audit_boards[0]

    return jsonify(
        id=audit_board.id, name=audit_board.name, members=serialize_members(audit_board)
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>",
    methods=["POST"],
)
@with_election_access
def set_audit_board(election, jurisdiction_id, audit_board_id):
    attributes = request.get_json()
    audit_boards = (
        AuditBoard.query.filter_by(id=audit_board_id)
        .join(Jurisdiction)
        .filter_by(id=jurisdiction_id, election_id=election.id)
        .all()
    )

    if not audit_boards:
        return (
            jsonify(
                errors=[
                    {
                        "message": f"No audit board found with id={audit_board_id}",
                        "errorType": "NotFoundError",
                    }
                ]
            ),
            404,
        )

    if len(audit_boards) > 1:
        return (
            jsonify(
                errors=[
                    {
                        "message": f"Found too many audit boards with id={audit_board_id}",
                        "errorType": "BadRequest",
                    }
                ]
            ),
            400,
        )

    audit_board = audit_boards[0]
    members = attributes.get("members", None)

    if members is not None:
        if len(members) != AUDIT_BOARD_MEMBER_COUNT:
            return (
                jsonify(
                    errors=[
                        {
                            "message": f"Members must contain exactly {AUDIT_BOARD_MEMBER_COUNT} entries, got {len(members)}",
                            "errorType": "BadRequest",
                        }
                    ]
                ),
                400,
            )

        for i in range(0, AUDIT_BOARD_MEMBER_COUNT):
            setattr(audit_board, f"member_{i + 1}", members[i]["name"])
            setattr(
                audit_board, f"member_{i + 1}_affiliation", members[i]["affiliation"]
            )

    name = attributes.get("name", None)

    if name is not None:
        audit_board.name = name

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballot-list"
)
@with_election_access
def ballot_list(election, jurisdiction_id, round_id):
    query = (
        SampledBallotDraw.query.join(SampledBallot)
        .join(SampledBallot.batch)
        .join(Round)
        .join(AuditBoard, AuditBoard.id == SampledBallot.audit_board_id)
        .add_entity(SampledBallot)
        .add_entity(Batch)
        .add_entity(AuditBoard)
        .filter(Round.id == round_id)
        .filter(Round.election_id == election.id)
        .filter(Batch.jurisdiction_id == jurisdiction_id)
        .order_by(
            AuditBoard.name,
            Batch.name,
            SampledBallot.ballot_position,
            SampledBallotDraw.ticket_number,
        )
        .all()
    )

    return jsonify(
        ballots=[
            {
                "ticketNumber": ballot_draw.ticket_number,
                "status": ballot.status,
                "interpretations": [
                    serialize_interpretation(i) for i in ballot.interpretations
                ],
                "position": ballot.ballot_position,
                "batch": {
                    "id": batch.id,
                    "name": batch.name,
                    "tabulator": batch.tabulator,
                },
                "auditBoard": {"id": audit_board.id, "name": audit_board.name},
            }
            for (ballot_draw, ballot, batch, audit_board) in query
        ]
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>/round/<round_id>/ballot-list"
)
@with_election_access
def ballot_list_by_audit_board(election, jurisdiction_id, audit_board_id, round_id):
    query = (
        SampledBallotDraw.query.join(Round)
        .join(SampledBallot)
        .join(Batch)
        .add_entity(SampledBallot)
        .add_entity(Batch)
        .filter(Round.id == round_id)
        .filter(Round.election_id == election.id)
        .filter(Batch.jurisdiction_id == jurisdiction_id)
        .filter(SampledBallot.audit_board_id == audit_board_id)
        .order_by(
            Batch.name, SampledBallot.ballot_position, SampledBallotDraw.ticket_number
        )
    )

    return jsonify(
        ballots=[
            {
                "ticketNumber": ballot_draw.ticket_number,
                "status": ballot.status,
                "interpretations": [
                    serialize_interpretation(i) for i in ballot.interpretations
                ],
                "position": ballot.ballot_position,
                "batch": {
                    "id": batch.id,
                    "name": batch.name,
                    "tabulator": batch.tabulator,
                },
            }
            for (ballot_draw, ballot, batch) in query
        ]
    )


def get_ballot(election_id, jurisdiction_id, batch_id, ballot_position):
    return (
        SampledBallot.query.filter_by(
            batch_id=batch_id, ballot_position=ballot_position
        )
        .join(SampledBallot.batch)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .filter(Jurisdiction.election_id == election_id)
        .one_or_none()
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch/<batch_id>/ballot/<ballot_position>/set-not-found",
    methods=["POST"],
)
@with_election_access
def ballot_set_not_found(election, jurisdiction_id, batch_id, ballot_position):
    ballot = get_ballot(election.id, jurisdiction_id, batch_id, ballot_position)

    if not ballot:
        return (
            jsonify(
                errors=[
                    {
                        "message": f"No ballot found with election_id={election.id}, jurisdiction_id={jurisdiction_id}, batch_id={batch_id}, ballot_position={ballot_position}",
                        "errorType": "NotFoundError",
                    }
                ]
            ),
            404,
        )

    # explicitly remove existing interpretations in case this ballot was previously set.
    ballot.interpretations = []
    ballot.status = BallotStatus.NOT_FOUND

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/batch/<batch_id>/ballot/<ballot_position>",
    methods=["POST"],
)
@with_election_access
def ballot_set(election, jurisdiction_id, batch_id, ballot_position):
    attributes = request.get_json()
    ballot = get_ballot(election.id, jurisdiction_id, batch_id, ballot_position)

    if not ballot:
        return (
            jsonify(
                errors=[
                    {
                        "message": f"No ballot found with election_id={election.id}, jurisdiction_id={jurisdiction_id}, batch_id={batch_id}, ballot_position={ballot_position}",
                        "errorType": "NotFoundError",
                    }
                ]
            ),
            404,
        )

    ballot.interpretations = [
        deserialize_interpretation(ballot.id, interpretation)
        for interpretation in attributes["interpretations"]
    ]
    ballot.status = BallotStatus.AUDITED

    db_session.commit()

    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/retrieval-list",
    methods=["GET"],
)
@with_election_access
def jurisdiction_retrieval_list(election, jurisdiction_id, round_num):
    # check the jurisdiction and round
    jurisdiction = Jurisdiction.query.filter_by(
        election_id=election.id, id=jurisdiction_id
    ).one()
    round = Round.query.filter_by(election_id=election.id, round_num=round_num).one()

    retrieval_list_csv = ballot_retrieval_list(jurisdiction, round)
    return csv_response(
        retrieval_list_csv,
        filename=f"ballot-retrieval-{election_timestamp_name(election)}.csv",
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/results",
    methods=["POST"],
)
@with_election_access
def jurisdiction_results(election, jurisdiction_id, round_num):
    results = request.get_json()

    # check the round ownership
    round = Round.query.filter_by(election_id=election.id, round_num=round_num).one()

    for contest in results["contests"]:
        RoundContest.query.filter_by(contest_id=contest["id"], round_id=round.id).one()
        RoundContestResult.query.filter_by(
            contest_id=contest["id"], round_id=round.id
        ).delete()

        for choice_id, result in contest["results"].items():
            contest_result = RoundContestResult(
                round_id=round.id,
                contest_id=contest["id"],
                contest_choice_id=choice_id,
                result=result,
            )
            db_session.add(contest_result)

    if not check_round(election, jurisdiction_id, round.id):
        setup_next_round(election)

    db_session.commit()

    return jsonify(status="ok")


@api.route("/election/<election_id>/audit/reset", methods=["POST"])
@with_election_access
def audit_reset(election):
    # deleting the election cascades to all the data structures
    db_session.delete(election)
    db_session.commit()

    election = Election(
        id=election.id,
        audit_name=election.audit_name,
        audit_type=election.audit_type,
        organization_id=election.organization_id,
        is_multi_jurisdiction=election.is_multi_jurisdiction,
    )
    db_session.add(election)
    db_session.commit()

    return jsonify(status="ok")
