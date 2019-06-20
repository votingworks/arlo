import os, datetime
from flask import Flask, send_from_directory, jsonify, request
from flask_sqlalchemy import SQLAlchemy

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

def init_db():
    db.create_all()
    e = Election(id=1, name="Election")
    db.session.add(e)
    db.session.commit()

def get_election():
    return Election.query.all()[0]
    

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
                        "name": choice.name,
                        "numVotes": choice.num_votes
                    }
                for choice in contest.choices]
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
                            "risk": round_contest.end_risk,
                            "pvalue": round_contest.end_p_value,
                            "isComplete": round_contest.is_complete
                        },
                        "results": dict([
                            [result.contest.id, result.result]
                            for result in round_contest.results]),
                        "minSampleSize": round_contest.min_sample_size,
                        "chosenSampleSize": round_contest.chosen_sample_size,
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

@app.route('/audit/sample-sizes', methods=["POST"])
def audit_set_sample_sizes():
    pass

@app.route('/jurisdiction/<jurisdiction_id>/manifest', methods=["DELETE","POST"])
def jurisdiction_manifest(jurisdiction_id):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    if not jurisdiction_id:
        return "no jurisdiction", 404

    if request.method == "DELETE":
        jurisdiction.manifest = None
        jurisdiction.manifest_filename = None
        jurisdiction.manifest_uploaded_at = None
        jurisdiction.manifest_num_ballots = None
        jurisdiction.manifest_num_batches = None
        db.session.commit()
        return jsonify(status="ok")

    manifest = request.files['manifest']
    jurisdiction.manifest_filename = manifest.filename
    jurisdiction.manifest_uploaded_at = datetime.datetime.utcnow()
    jurisdiction.manifest = manifest.read()

    return jsonify(status="ok")

@app.route('/jurisdiction/<jurisdiction_id>/results', methods=["POST"])
def jurisdiction_results(jurisdiction_id):
    pass

@app.route('/jurisdiction/<jurisdiction_id>/retrieval-list', methods=["GET"])
def jurisdiction_retrieval_list(jurisdiction_id):
    pass

@app.route('/audit/report', methods=["GET"])
def audit_report():
    pass



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
