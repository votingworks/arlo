import os, datetime, csv, io, math, json, uuid, locale, re
from flask import Flask, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from sampler import Sampler
from werkzeug.exceptions import InternalServerError

from sqlalchemy import event
from config import DATABASE_URL

from util.binpacking import Bucket, BalancedBucketList

app = Flask(__name__, static_folder='arlo-client/build/')

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

AUDIT_BOARD_MEMBER_COUNT = 2

def create_election(election_id=None):
    if not election_id:
        election_id = str(uuid.uuid4())
    e = Election(id=election_id, name="")
    db.session.add(e)
    db.session.commit()
    return election_id

def init_db():
    db.create_all()

def get_election(election_id):
    return Election.query.filter_by(id = election_id).one()

def contest_status(election):
    contests = {}

    for contest in election.contests:
        contests[contest.id] = dict([
            [choice.id, choice.num_votes]
            for choice in contest.choices])
        contests[contest.id]['ballots'] = contest.total_ballots_cast
        contests[contest.id]['numWinners'] = contest.num_winners
        contests[contest.id]['votesAllowed'] = contest.votes_allowed

    return contests

def sample_results(election):
    contests = {}

    for contest in election.contests:
        contests[contest.id] = dict([
            [choice.id, 0]
            for choice in contest.choices])

        round_contests = RoundContest.query.filter_by(contest_id = contest.id).order_by('round_id').all()
        for round_contest in round_contests:
            for result in round_contest.results:
                contests[contest.id][result.targeted_contest_choice_id] += result.result

    return contests

def manifest_summary(jurisdiction):
    manifest = {}

    for batch in jurisdiction.batches:
        manifest[batch.id] = batch.num_ballots

    return manifest

def get_sampler(election):
    # TODO Change this to audit_type
    return Sampler('BRAVO', election.random_seed, election.risk_limit / 100, contest_status(election))

def compute_sample_sizes(round_contest):
    the_round = round_contest.round
    election = the_round.election
    sampler = get_sampler(election)

    # format the options properly
    raw_sample_size_options = sampler.get_sample_sizes(sample_results(election))[election.contests[0].id]
    sample_size_options = []
    sample_size_90 = None
    sample_size_backup = None
    for (prob_or_asn, size) in raw_sample_size_options.items():
        prob = None
        type = None

        if prob_or_asn == "asn":
            if size["prob"]:
                prob = round(size["prob"], 2), # round to the nearest hundreth 
            sample_size_options.append({
                "type": "ASN",
                "prob": prob,
                "size": int(math.ceil(size["size"]))
            })
            sample_size_backup = int(math.ceil(size["size"]))

        else:
            prob = prob_or_asn
            sample_size_options.append({
                "type": None,
                "prob": prob,
                "size": int(math.ceil(size))
            })

            # stash this one away for later
            if prob == 0.9:
                sample_size_90 = size
    
    round_contest.sample_size_options = json.dumps(sample_size_options)

    # if we are in multi-winner, there is no sample_size_90 so fix it
    if not sample_size_90:
        sample_size_90 = sample_size_backup

    # for later rounds, we always pick 90%
    if round_contest.round.round_num > 1:
        round_contest.sample_size = sample_size_90        
        sample_ballots(election, the_round)

    db.session.commit()
        
def setup_next_round(election):
    if len(election.contests) > 1:
        raise Exception("only supports one contest for now")

    rounds = Round.query.filter_by(election_id = election.id).order_by('round_num').all()

    print("adding round {:d} for election {:s}".format(len(rounds)+1, election.id))
    round = Round(
        id = str(uuid.uuid4()),
        election_id = election.id,
        round_num = len(rounds) + 1,
        started_at = datetime.datetime.utcnow())

    db.session.add(round)

    # assume just one contest for now
    contest = election.contests[0]
    round_contest = RoundContest(
        round_id = round.id,
        contest_id = contest.id
    )

    db.session.add(round_contest)

def sample_ballots(election, round):
    # assume only one contest
    round_contest = round.round_contests[0]
    jurisdiction = election.jurisdictions[0]
    
    num_sampled = db.session.query(db.func.sum(SampledBallot.times_sampled)).filter_by(jurisdiction_id=jurisdiction.id).one()[0]
    if not num_sampled:
        num_sampled = 0

    chosen_sample_size = round_contest.sample_size
    sampler = get_sampler(election)
    sample = sampler.draw_sample(manifest_summary(jurisdiction), chosen_sample_size, num_sampled=num_sampled)

    audit_boards = jurisdiction.audit_boards
    
    last_sample = None
    last_sampled_ballot = None

    batch_sizes = {}
    batches_to_ballots = {}
    seen_ballot_positions = set()
    # Build batch - batch_size map
    for batch_id, ballot_position in sample:

        lookup = (batch_id, ballot_position)
        # Only count ballots once here since it's only pulled once
        if lookup in seen_ballot_positions:
            batches_to_ballots[batch_id].append(ballot_position)
            continue

        seen_ballot_positions.add(lookup)
        if batch_id in batch_sizes:
            batch_sizes[batch_id] += 1
            batches_to_ballots[batch_id].append(ballot_position)
        else:
            batch_sizes[batch_id] = 1
            batches_to_ballots[batch_id] = [ballot_position]

    # Create the buckets and initially assign batches
    buckets = []
    for audit_board in audit_boards:
        buckets.append(Bucket(audit_board.name))

    for i, batch in enumerate(batch_sizes):
        buckets[i%len(audit_boards)].add_batch(batch, batch_sizes[batch])

    # Now assign batchest fairly
    bl = BalancedBucketList(buckets)

    # read audit board and batch info out
    for bucket in bl.buckets:
        audit_board_num = bl.buckets.index(bucket)
        audit_board = audit_boards[audit_board_num]
        for batch_id in bucket.batches:

            for ballot_position in batches_to_ballots[batch_id]:
                if last_sample == (batch_id, ballot_position):
                    last_sampled_ballot.times_sampled += 1
                    continue

                sampled_ballot = SampledBallot(
                        round_id = round.id,
                        jurisdiction_id = jurisdiction.id,
                        batch_id = batch_id,
                        ballot_position = ballot_position + 1, # sampler is 0-indexed, we're 1-indexing here
                        times_sampled = 1,
                        audit_board_id = audit_board.id)

                # keep track for doubly-sampled ballots
                last_sample = (batch_id, ballot_position)
                last_sampled_ballot = sampled_ballot

                db.session.add(sampled_ballot)
    
    db.session.commit()
        

def check_round(election, jurisdiction_id, round_id):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    round = Round.query.get(round_id)

    # assume one contest
    round_contest = round.round_contests[0]
    
    sampler = get_sampler(election)
    current_sample_results = sample_results(election)

    risk, is_complete = sampler.compute_risk(round_contest.contest_id, current_sample_results[round_contest.contest_id])

    round.ended_at = datetime.datetime.utcnow()
    # TODO this is a hack, should we report pairwise p-values?
    round_contest.end_p_value = max(risk.values())
    round_contest.is_complete = is_complete

    db.session.commit()

    return is_complete

def election_timestamp_name(election) -> str:
    clean_election_name = re.sub(r'[^a-zA-Z0-9]+', r'-', election.name)
    now = datetime.datetime.utcnow().isoformat(timespec='minutes')
    return f'{clean_election_name}-{now}'

@app.route('/election/new', methods=["POST"])
def election_new():
    election_id = create_election()
    return jsonify(electionId = election_id)

@app.route('/election/<election_id>/audit/status', methods=["GET"])
def audit_status(election_id = None):
    election = get_election(election_id)

    return jsonify(
        name = election.name,
        riskLimit = election.risk_limit,
        randomSeed = election.random_seed,
        contests = [
            {
                "id": contest.id,
                "name": contest.name,
                "choices": [
                    {
                        "id": choice.id,
                        "name": choice.name,
                        "numVotes": choice.num_votes
                    }
                    for choice in contest.choices],
                "totalBallotsCast": contest.total_ballots_cast,
                "numWinners": contest.num_winners,
                "votesAllowed": contest.votes_allowed
            }
            for contest in election.contests],
        jurisdictions=[
            {
                "id": j.id,
                "name": j.name,
                "contests": [c.contest_id for c in j.contests],
                "auditBoards": [
                    {
                        "id": audit_board.id,
                        "name": audit_board.name,
                        "members": []
                    }
                    for audit_board in j.audit_boards],
                "ballotManifest": {
                    "filename": j.manifest_filename,
                    "numBallots": j.manifest_num_ballots,
                    "numBatches": j.manifest_num_batches,
                    "uploadedAt": j.manifest_uploaded_at
                },
                "batches": [
                    {
                        "id": batch.id,
                        "name": batch.name,
                        "numBallots": batch.num_ballots,
                        "storageLocation": batch.storage_location,
                        "tabulator": batch.tabulator
                    }
                    for batch in j.batches
                ]
            }
            for j in election.jurisdictions],
        rounds=[
            {
                "id": round.id,
                "startedAt": round.started_at,
                "endedAt": round.ended_at,
                "contests": [
                    {
                        "id": round_contest.contest_id,
                        "endMeasurements": {
                            "pvalue": round_contest.end_p_value,
                            "isComplete": round_contest.is_complete
                        },
                        "results": dict([
                            [result.targeted_contest_choice_id, result.result]
                            for result in round_contest.results]),
                        "sampleSizeOptions": json.loads(round_contest.sample_size_options or 'null'),
                        "sampleSize": round_contest.sample_size
                    }
                    for round_contest in round.round_contests
                ]
            }
            for round in election.rounds
        ]
    )

@app.route('/election/<election_id>/audit/basic', methods=["POST"])
def audit_basic_update(election_id):
    election = get_election(election_id)
    info = request.get_json()
    election.name = info['name']
    election.risk_limit = info['riskLimit']
    election.random_seed = info['randomSeed']

    errors = []
    db.session.query(TargetedContest).filter_by(election_id = election.id).delete()

    for contest in info['contests']:
        total_allowed_votes_in_contest = contest['totalBallotsCast'] * contest['votesAllowed']

        contest_obj = TargetedContest(election_id = election.id,
                             id = contest['id'],
                             name = contest['name'],
                             total_ballots_cast = contest['totalBallotsCast'],
                             num_winners = contest['winners'],
                             votes_allowed = contest['votesAllowed'])
        db.session.add(contest_obj)

        total_votes_in_all_choices = 0

        for choice in contest['choices']:
            total_votes_in_all_choices += choice['numVotes']

            choice_obj = TargetedContestChoice(id = choice['id'],
                                               contest_id = contest_obj.id,
                                               name = choice['name'],
                                               num_votes = choice['numVotes'])
            db.session.add(choice_obj)

        if total_votes_in_all_choices > total_allowed_votes_in_contest:
            errors.append({
                'message': f'Too many votes cast in contest: {contest["name"]} ({total_votes_in_all_choices} votes, {total_allowed_votes_in_contest} allowed)',
                'errorType': 'TooManyVotes'
            })

    if errors:
        db.session.rollback()
        return jsonify(errors=errors), 400

    # prepare the round, including sample sizes
    setup_next_round(election)
            
    db.session.commit()

    return jsonify(status="ok")

@app.route('/election/<election_id>/audit/sample-size', methods=["POST"])
def samplesize_set(election_id):
    election = get_election(election_id)

    # only works if there's only one round
    rounds = election.rounds
    if len(rounds) > 1:
        return jsonify(status="bad")

    rounds[0].round_contests[0].sample_size = int(request.get_json()['size'])
    db.session.commit()

    return jsonify(status="ok")


@app.route('/election/<election_id>/audit/jurisdictions', methods=["POST"])
def jurisdictions_set(election_id):
    election = get_election(election_id)
    jurisdictions = request.get_json()['jurisdictions']
    
    db.session.query(Jurisdiction).filter_by(election_id = election.id).delete()

    for jurisdiction in jurisdictions:
        jurisdiction_obj = Jurisdiction(
            election_id = election.id,
            id = jurisdiction['id'],
            name = jurisdiction['name']
        )
        db.session.add(jurisdiction_obj)

        for contest_id in jurisdiction["contests"]:
            jurisdiction_contest = TargetedContestJurisdiction(
                contest_id = contest_id,
                jurisdiction_id = jurisdiction_obj.id
            )
            db.session.add(jurisdiction_contest)

        for audit_board in jurisdiction["auditBoards"]:
            audit_board_obj = AuditBoard(
                id = audit_board["id"],
                name = audit_board["name"],
                jurisdiction_id = jurisdiction_obj.id
            )
            db.session.add(audit_board_obj)
        
    db.session.commit()

    return jsonify(status="ok")

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/manifest', methods=["DELETE","POST"])
def jurisdiction_manifest(jurisdiction_id, election_id):
    BATCH_NAME = 'Batch Name'
    NUMBER_OF_BALLOTS = 'Number of Ballots'
    STORAGE_LOCATION = 'Storage Location'
    TABULATOR = 'Tabulator'

    election = get_election(election_id)
    jurisdiction = Jurisdiction.query.filter_by(election_id = election.id, id = jurisdiction_id).one()

    if not jurisdiction:
        return jsonify(errors=[
            {
                'message': f'No jurisdiction found with id: {jurisdiction_id}',
                'errorType': 'NotFoundError'
            }
        ]), 404

    if request.method == "DELETE":
        jurisdiction.manifest = None
        jurisdiction.manifest_filename = None
        jurisdiction.manifest_uploaded_at = None
        jurisdiction.manifest_num_ballots = None
        jurisdiction.manifest_num_batches = None

        Batch.query.filter_by(jurisdiction = jurisdiction).delete()
        
        db.session.commit()
        
        return jsonify(status="ok")

    manifest_bytesio = io.BytesIO()
    manifest = request.files['manifest']
    manifest.save(manifest_bytesio)
    manifest_string = manifest_bytesio.getvalue().decode('utf-8-sig')
    jurisdiction.manifest = manifest_string

    jurisdiction.manifest_filename = manifest.filename
    jurisdiction.manifest_uploaded_at = datetime.datetime.utcnow()

    manifest_csv = csv.DictReader(io.StringIO(manifest_string))

    missing_fields = [field for field in [BATCH_NAME, NUMBER_OF_BALLOTS] if field not in manifest_csv.fieldnames]

    if missing_fields:
        return jsonify(errors=[
            {
                'message': f'Missing required CSV field "{field}"',
                'errorType': 'MissingRequiredCsvField',
                'fieldName': field
            }
            for field in missing_fields
        ]), 400

    num_batches = 0
    num_ballots = 0
    for row in manifest_csv:
        num_ballots_in_batch_csv = row[NUMBER_OF_BALLOTS]

        try:
            num_ballots_in_batch = locale.atoi(num_ballots_in_batch_csv)
        except:
            return jsonify(errors=[
                {
                    'message': f'Invalid value for "{NUMBER_OF_BALLOTS}" on line {manifest_csv.line_num}: {num_ballots_in_batch_csv}',
                    'errorType': 'InvalidCsvIntegerField'
                }
            ]), 400

        batch = Batch(
            id = str(uuid.uuid4()),
            name = row[BATCH_NAME],
            jurisdiction_id = jurisdiction.id,
            num_ballots = num_ballots_in_batch,
            storage_location = row.get(STORAGE_LOCATION, None),
            tabulator = row.get(TABULATOR, None)
        )
        db.session.add(batch)
        num_batches += 1
        num_ballots += batch.num_ballots

    jurisdiction.manifest_num_ballots = num_ballots
    jurisdiction.manifest_num_batches = num_batches
    db.session.commit()

    # draw the sample
    sample_ballots(election, election.rounds[0])
    
    return jsonify(status="ok")

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>', methods=["GET"])
def audit_board(election_id, jurisdiction_id, audit_board_id):
    audit_boards = AuditBoard.query.filter_by(id=audit_board_id) \
        .join(Jurisdiction).filter_by(id=jurisdiction_id, election_id=election_id) \
        .all()

    if not audit_boards:
        return f"no audit board found with id={audit_board_id}", 404

    if len(audit_boards) > 1:
        return f"found too many audit boards with id={audit_board_id}", 400

    audit_board = audit_boards[0]

    members = []

    for i in range(0, AUDIT_BOARD_MEMBER_COUNT):
        name = getattr(audit_board, f"member_{i + 1}")
        affiliation = getattr(audit_board, f"member_{i + 1}_affiliation")

        if not name:
            break

        members.append({
            "name": name,
            "affiliation": affiliation
        })

    return jsonify(
        id=audit_board.id,
        name=audit_board.name,
        members=members
    )

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>', methods=["POST"])
def set_audit_board(election_id, jurisdiction_id, audit_board_id):
    try:
        attributes = request.get_json()
    except:
        return jsonify(errors=[
            {
                'message': 'Could not parse JSON',
                'errorType': 'BadRequest'
            }
        ]), 400

    audit_boards = AuditBoard.query.filter_by(id=audit_board_id) \
        .join(Jurisdiction).filter_by(id=jurisdiction_id, election_id=election_id) \
        .all()

    if not audit_boards:
        return jsonify(errors=[
            {
                'message': f'No audit board found with id={audit_board_id}',
                'errorType': 'NotFoundError'
            }
        ]), 404

    if len(audit_boards) > 1:
        return jsonify(errors=[
            {
                'message': f'Found too many audit boards with id={audit_board_id}',
                'errorType': 'BadRequest'
            }
        ]), 400

    audit_board = audit_boards[0]
    members = attributes.get('members', None)

    if members is not None:
        if len(members) != AUDIT_BOARD_MEMBER_COUNT:
            return jsonify(errors=[
                {
                    'message': f'Members must contain exactly {AUDIT_BOARD_MEMBER_COUNT} entries, got {len(members)}',
                    'errorType': 'BadRequest'
                }
            ]), 400

        for i in range(0, AUDIT_BOARD_MEMBER_COUNT):
            setattr(audit_board, f"member_{i + 1}", members[i]['name'])
            setattr(audit_board, f"member_{i + 1}_affiliation", members[i]['affiliation'])

    name = attributes.get('name', None)

    if name is not None:
        audit_board.name = name

    db.session.commit()

    return jsonify(status="ok")

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballot-list')
def ballot_list(election_id, jurisdiction_id, round_id):
    query = db.session.query(AuditBoard, Batch, SampledBallot) \
        .filter(Batch.id == SampledBallot.batch_id) \
        .filter(SampledBallot.jurisdiction_id == jurisdiction_id) \
        .filter(SampledBallot.round_id == round_id) \
        .order_by(AuditBoard.name, Batch.name, SampledBallot.ballot_position)

    return jsonify(
        ballots=[
            {
                "timesSampled": ballot.times_sampled,
                "status": 'AUDITED' if ballot.vote is not None else None,
                "vote": ballot.vote,
                "comment": ballot.comment,
                "position": ballot.ballot_position,
                "batch": {
                    "id": batch.id,
                    "name": batch.name,
                    "tabulator": batch.tabulator
                },
                "auditBoard": {
                    "id": audit_board.id,
                    "name": audit_board.name
                }
            }
            for (audit_board, batch, ballot) in query
        ]
    )

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>/round/<round_id>/ballot-list')
def ballot_list_by_audit_board(election_id, jurisdiction_id, audit_board_id, round_id):
    query = db.session.query(Batch, SampledBallot) \
        .filter(Batch.id == SampledBallot.batch_id) \
        .filter(SampledBallot.jurisdiction_id == jurisdiction_id) \
        .filter(SampledBallot.audit_board_id == audit_board_id) \
        .filter(SampledBallot.round_id == round_id) \
        .order_by(Batch.name, SampledBallot.ballot_position)

    return jsonify(
        ballots=[
            {
                "timesSampled": ballot.times_sampled,
                "status": 'AUDITED' if ballot.vote is not None else None,
                "vote": ballot.vote,
                "comment": ballot.comment,
                "position": ballot.ballot_position,
                "batch": {
                    "id": batch.id,
                    "name": batch.name,
                    "tabulator": batch.tabulator
                }
            }
            for (batch, ballot) in query
        ]
    )

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/batch/<batch_id>/round/<round_id>/ballot/<ballot_position>', methods=["POST"])
def ballot_set(election_id, jurisdiction_id, batch_id, round_id, ballot_position):
    try:
        attributes = request.get_json()
    except:
        return jsonify(errors=[
            {
                'message': 'Could not parse JSON',
                'errorType': 'BadRequest'
            }
        ]), 400

    ballots = SampledBallot \
        .query.filter_by(jurisdiction_id=jurisdiction_id, batch_id=batch_id, ballot_position=ballot_position) \
        .join(Round).filter_by(election_id=election_id, id=round_id) \
        .all()

    if not ballots:
        return jsonify(errors=[
            {
                'message': f'No ballot found with election_id={election_id}, jurisdiction_id={jurisdiction_id}, batch_id={batch_id}, ballot_position={ballot_position}, round={round_id}',
                'errorType': 'NotFoundError'
            }
        ]), 404
    elif len(ballots) > 1:
        return jsonify(errors=[
            {
                'message': f'Multiple ballots found with election_id={election_id}, jurisdiction_id={jurisdiction_id}, batch_id={batch_id}, ballot_position={ballot_position}, round={round_id}',
                'errorType': 'BadRequest'
            }
        ]), 400

    ballot = ballots[0]

    if 'vote' in attributes:
        ballot.vote = attributes['vote']

    if 'comment' in attributes:
        ballot.comment = attributes['comment']

    db.session.commit()

    return jsonify(status="ok")

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/retrieval-list', methods=["GET"])
def jurisdiction_retrieval_list(election_id, jurisdiction_id, round_num):
    election = get_election(election_id)
    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerow(["Batch Name","Ballot Number","Storage Location","Tabulator","Times Selected","Audit Board"])

    # check the jurisdiction and round
    jurisdiction = Jurisdiction.query.filter_by(election_id = election.id, id = jurisdiction_id).one()
    round = Round.query.filter_by(election_id = election.id, round_num = round_num).one()

    ballots = SampledBallot.query.filter_by(jurisdiction_id = jurisdiction_id, round_id = round.id).join(Batch).join(AuditBoard).order_by(AuditBoard.name, Batch.name, 'ballot_position').all()

    for ballot in ballots:
        retrieval_list_writer.writerow([ballot.batch.name, ballot.ballot_position, ballot.batch.storage_location, ballot.batch.tabulator, ballot.times_sampled, ballot.audit_board.name])

    response = Response(csv_io.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="ballot-retrieval-{election_timestamp_name(election)}.csv"'
    return response

@app.route('/election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/results', methods=["POST"])
def jurisdiction_results(election_id, jurisdiction_id, round_num):
    election = get_election(election_id)
    results = request.get_json()

    # check the round ownership
    round = Round.query.filter_by(election_id = election.id, round_num = round_num).one()
    
    for contest in results["contests"]:
        round_contest = RoundContest.query.filter_by(contest_id = contest["id"], round_id = round.id).one()
        RoundContestResult.query.filter_by(contest_id = contest["id"], round_id = round.id).delete()

        for choice_id, result in contest["results"].items():
            contest_result = RoundContestResult(
                round_id = round.id,
                contest_id = contest["id"],
                targeted_contest_choice_id = choice_id,
                result = result)
            db.session.add(contest_result)

    if not check_round(election, jurisdiction_id, round.id):
        setup_next_round(election)

    db.session.commit()
        
    return jsonify(status="ok")

@app.route('/election/<election_id>/audit/report', methods=["GET"])
def audit_report(election_id):
    election = get_election(election_id)
    jurisdiction = election.jurisdictions[0]

    csv_io = io.StringIO()
    report_writer = csv.writer(csv_io)

    contest = election.contests[0]
    choices = contest.choices
    
    report_writer.writerow(["Contest Name", contest.name])
    report_writer.writerow(["Number of Winners", contest.num_winners])
    report_writer.writerow(["Votes Allowed", contest.votes_allowed])
    report_writer.writerow(["Total Ballots Cast", contest.total_ballots_cast])

    for choice in choices:
        report_writer.writerow(["{:s} Votes".format(choice.name), choice.num_votes])

    report_writer.writerow(["Risk Limit", "{:d}%".format(election.risk_limit)])
    report_writer.writerow(["Random Seed", election.random_seed])

    for round in election.rounds:
        round_contest = round.round_contests[0]
        round_contest_results = round_contest.results

        report_writer.writerow(["Round {:d} Sample Size".format(round.round_num), round_contest.sample_size])

        for result in round_contest.results:
            report_writer.writerow(["Round {:d} Audited Votes for {:s}".format(round.round_num, result.targeted_contest_choice.name), result.result])

        report_writer.writerow(["Round {:d} P-Value".format(round.round_num), round_contest.end_p_value])
        report_writer.writerow(["Round {:d} Risk Limit Met?".format(round.round_num), 'Yes' if round_contest.is_complete else 'No'])

        report_writer.writerow(["Round {:d} Start".format(round.round_num), round.started_at])
        report_writer.writerow(["Round {:d} End".format(round.round_num), round.ended_at])

        ballots = SampledBallot.query.filter_by(jurisdiction_id = jurisdiction.id, round_id = round.id).order_by('batch_id', 'ballot_position').all()

        report_writer.writerow(["Round {:d} Samples".format(round.round_num), " ".join(["(Batch {:s}, #{:d})".format(b.batch.name, b.ballot_position) for b in ballots])])

    
    response = Response(csv_io.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="audit-report-{election_timestamp_name(election)}.csv"'
    return response
    

@app.route('/election/<election_id>/audit/reset', methods=["POST"])
def audit_reset(election_id):
    # deleting the election cascades to all the data structures
    Election.query.filter_by(id = election_id).delete()
    db.session.commit()

    create_election(election_id)
    db.session.commit()
    
    return jsonify(status="ok")


# React App
@app.route('/')
@app.route('/election/<election_id>')
def serve(election_id=None):
    return app.send_static_file('index.html')

@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return e

    # wrapped unhandled error
    return jsonify(errors=[
        {
            'message': str(original),
            'errorType': type(original).__name__
        }
    ]), 500


if __name__ == '__main__':
    app.run(use_reloader=True, port=os.environ.get('PORT',3001), host='0.0.0.0', threaded=True)
