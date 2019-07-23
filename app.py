import os, datetime, csv, io, math
from flask import Flask, send_from_directory, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from sampler import Sampler

app = Flask(__name__, static_folder='arlo-client/build/')

# database config
SQLITE_DATABASE_URL = 'sqlite:///./arlo.db'
database_url = os.environ.get('DATABASE_URL', SQLITE_DATABASE_URL)
if database_url == "":
    database_url = SQLITE_DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

def create_election():
    e = Election(id=1, name="Election")
    db.session.add(e)
    db.session.commit()

def init_db():
    db.create_all()
    create_election()

def get_election():
    return Election.query.all()[0]

def contest_status(election):
    contests = {}

    for contest in election.contests:
        contests[contest.id] = dict([
            [choice.id, choice.num_votes]
            for choice in contest.choices])
        contests[contest.id]['ballots'] = contest.total_ballots_cast

    return contests

def sample_results(election):
    contests = {}

    for contest in election.contests:
        contests[contest.id] = dict([
            [choice.id, 0]
            for choice in contest.choices])

        # now add in all the results
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
    return Sampler(election.random_seed, election.risk_limit / 100, contest_status(election))

def setup_next_round(election):
    jurisdiction = election.jurisdictions[0]
    rounds = Round.query.filter_by(election_id = election.id).order_by('id').all()

    round = Round(
        id = len(rounds) + 1,
        election_id = election.id,
        started_at = datetime.datetime.utcnow())

    db.session.add(round)

    sampler = get_sampler(election)
    sample_sizes = sampler.get_sample_sizes(sample_results(election))
    
    # all contests for now
    chosen_sample_size = None
    for contest in election.contests:
        round_contest = RoundContest(
            round_id = round.id,
            contest_id = contest.id
        )

        round_contest.sample_size = sample_sizes[contest.id]['90%']
        chosen_sample_size = round_contest.sample_size

        db.session.add(round_contest)
    
    sample = sampler.draw_sample(manifest_summary(jurisdiction), chosen_sample_size)

    audit_boards = jurisdiction.audit_boards
    
    last_sample = None
    last_sampled_ballot = None
    
    for sample_number, (batch_id, ballot_position) in enumerate(sample):
        if last_sample == (batch_id, ballot_position):
            last_sampled_ballot.times_sampled += 1
            continue
        
        audit_board_num = math.floor(len(audit_boards) * sample_number / len(sample))
        audit_board = audit_boards[audit_board_num]
        sampled_ballot = SampledBallot(
            round_id = round.id,
            jurisdiction_id = jurisdiction.id,
            batch_id = batch_id,
            ballot_position = ballot_position,
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
    round_contest.end_p_value = risk
    round_contest.is_complete = is_complete

    db.session.commit()
    
    if not is_complete:
        setup_next_round(election)

# get/set audit config
# state and jurisdictions[]
@app.route('/audit/status', methods=["GET"])
def audit_status():
    election = get_election()

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
                "totalBallotsCast": contest.total_ballots_cast
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
                        "members": []
                    }
                    for audit_board in j.audit_boards],
                "ballotManifest": {
                    "filename": j.manifest_filename,
                    "numBallots": j.manifest_num_ballots,
                    "numBatches": j.manifest_num_batches,
                    "uploadedAt": j.manifest_uploaded_at
                }
            }
            for j in election.jurisdictions],
        rounds=[
            {
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
                        "sampleSize": round_contest.sample_size
                    }
                    for round_contest in round.round_contests
                ]
            }
            for round in election.rounds
        ]
    )

@app.route('/audit/basic', methods=["POST"])
def audit_basic_update():
    election = get_election()
    info = request.get_json()
    election.name = info['name']
    election.risk_limit = info['riskLimit']
    election.random_seed = info['randomSeed']

    db.session.query(TargetedContest).filter_by(election_id = election.id).delete()

    for contest in info['contests']:
        contest_obj = TargetedContest(election_id = election.id,
                             id = contest['id'],
                             name = contest['name'],
                             total_ballots_cast = contest['totalBallotsCast'])
        db.session.add(contest_obj)

        for choice in contest['choices']:
            choice_obj = TargetedContestChoice(id = choice['id'],
                                               contest_id = contest_obj.id,
                                               name = choice['name'],
                                               num_votes = choice['numVotes'])
            db.session.add(choice_obj)

    db.session.commit()

    return jsonify(status="ok")

@app.route('/audit/jurisdictions', methods=["POST"])
def jurisdictions_set():
    election = get_election()
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
                jurisdiction_id = jurisdiction_obj.id
            )
            db.session.add(audit_board_obj)
        
    db.session.commit()

    return jsonify(status="ok")

@app.route('/jurisdiction/<jurisdiction_id>/manifest', methods=["DELETE","POST"])
def jurisdiction_manifest(jurisdiction_id):
    election = get_election()
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    if not jurisdiction:
        return "no jurisdiction", 404

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

    # TODO: factor out manifest processing for more intensive testing and background processing
    manifest_csv = csv.DictReader(io.StringIO(manifest_string))
    num_batches = 0
    num_ballots = 0
    for row in manifest_csv:
        batch = Batch(
            id = row['Batch Name'],
            name = row['Batch Name'],
            jurisdiction_id = jurisdiction.id,
            num_ballots = int(row['Number of Ballots']),
            storage_location = row.get('Storage Location', None),
            tabulator = row.get('Tabulator', None)
        )
        db.session.add(batch)
        num_batches += 1
        num_ballots += batch.num_ballots

    jurisdiction.manifest_num_ballots = num_ballots
    jurisdiction.manifest_num_batches = num_batches
    db.session.commit()

    # get the next round setup
    setup_next_round(election)
    
    return jsonify(status="ok")

@app.route('/jurisdiction/<jurisdiction_id>/<round_id>/retrieval-list', methods=["GET"])
def jurisdiction_retrieval_list(jurisdiction_id, round_id):
    csv_io = io.StringIO()
    retrieval_list_writer = csv.writer(csv_io)
    retrieval_list_writer.writerow(["Batch Name","Ballot Number","Storage Location","Tabulator","Times Selected","Audit Board"])

    ballots = SampledBallot.query.filter_by(jurisdiction_id = jurisdiction_id, round_id = int(round_id)).order_by('batch_id', 'ballot_position').all()

    for ballot in ballots:
        retrieval_list_writer.writerow([ballot.batch_id, ballot.ballot_position, ballot.batch.storage_location, ballot.batch.tabulator, ballot.times_sampled, ballot.audit_board_id])

    response = Response(csv_io.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename="ballot-retrieval-{:s}-{:s}.csv"'.format(jurisdiction_id, round_id)
    return response

@app.route('/jurisdiction/<jurisdiction_id>/<round_id>/results', methods=["POST"])
def jurisdiction_results(jurisdiction_id, round_id):
    election = get_election()
    results = request.get_json()

    for contest in results["contests"]:
        round_contest = RoundContest.query.filter_by(contest_id = contest["id"], round_id = round_id).one()
        RoundContestResult.query.filter_by(contest_id = contest["id"], round_id = round_id).delete()

        for choice_id, result in contest["results"].items():
            contest_result = RoundContestResult(
                round_id = round_id,
                contest_id = contest["id"],
                targeted_contest_choice_id = choice_id,
                result = result)
            db.session.add(contest_result)

    db.session.commit()

    check_round(election, jurisdiction_id, round_id)

    return jsonify(status="ok")

@app.route('/audit/report', methods=["GET"])
def audit_report():
    election = get_election()
    jurisdiction = election.jurisdictions[0]

    csv_io = io.StringIO()
    report_writer = csv.writer(csv_io)

    contest = election.contests[0]
    choices = contest.choices
    
    report_writer.writerow(["Contest Name", contest.name])
    report_writer.writerow(["Total Ballots Cast", contest.total_ballots_cast])

    for choice in choices:
        report_writer.writerow(["{:s} Votes".format(choice.name), choice.num_votes])

    report_writer.writerow(["Risk Limit", "{:d}%".format(election.risk_limit)])
    report_writer.writerow(["Random Seed", election.random_seed])

    for round in election.rounds:
        round_contest = round.round_contests[0]
        round_contest_results = round_contest.results

        report_writer.writerow(["Round {:d} Sample Size".format(round.id), round_contest.sample_size])

        for result in round_contest.results:
            report_writer.writerow(["Round {:d} Audited Votes for {:s}".format(round.id, result.targeted_contest_choice.name), result.result])

        report_writer.writerow(["Round {:d} P-Value".format(round.id), round_contest.end_p_value])
        report_writer.writerow(["Round {:d} Risk Limit Met?".format(round.id), 'Yes' if round_contest.is_complete else 'No'])

        report_writer.writerow(["Round {:d} Start".format(round.id), round.started_at])
        report_writer.writerow(["Round {:d} End".format(round.id), round.ended_at])

        ballots = SampledBallot.query.filter_by(jurisdiction_id = jurisdiction.id, round_id = round.id).order_by('batch_id', 'ballot_position').all()

        report_writer.writerow(["Round {:d} Samples".format(round.id), " ".join(["(Batch {:s}, #{:d})".format(b.batch_id, b.ballot_position) for b in ballots])])

    
    response = Response(csv_io.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename="audit-report.csv"'
    return response
    

@app.route('/audit/reset', methods=["POST"])
def audit_reset():
    SampledBallot.query.delete()
    AuditBoard.query.delete()
    Batch.query.delete()
    RoundContestResult.query.delete()
    RoundContest.query.delete()
    Round.query.delete()
    TargetedContestJurisdiction.query.delete()
    TargetedContestChoice.query.delete()
    TargetedContest.query.delete()
    Jurisdiction.query.delete()
    User.query.delete()
    Election.query.delete()
    
    db.session.commit()
    create_election()
    db.session.commit()   
    return jsonify(status="ok")


# React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(use_reloader=True, port=os.environ.get('PORT',3001), host='0.0.0.0', threaded=True)
