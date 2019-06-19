import os
from flask import Flask, send_from_directory, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='arlo-client/build/')

# database config
SQLITE_DATABASE_URL = 'sqlite:///./arlo.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', SQLITE_DATABASE_URL)
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
    if request.method == 'POST':
        election_info = request.get_json()
        election.name = election_info['name']
        db.session.query(Jurisdiction).filter_by(election_id = election.id).delete()
        for jurisdiction in election_info['jurisdictions']:
            j = Jurisdiction(
                election_id = election.id,
                name = jurisdiction)
            db.session.add(j)

        db.session.commit()

    return jsonify(
        id=election.id,
        name=election.name,
        jurisdictions=[j.name for j in election.jurisdictions])

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
    
@app.route('/jurisdiction/<jurisdiction_id>/manifest')
def jurisdiction_manifest(jurisdiction_id):
    pass

@app.route('/jurisdiction/<jurisdiction_id>/auditboards')
def jurisdiction_auditboards(jurisdiction_id):
    pass

@app.route('/jurisdiction/<jurisdiction_id>/auditboard/<audit_board_id>')
def jurisdiction_auditboard(jurisdiction_id, audit_board_id):
    pass

@app.route('/jurisdiction/<jurisdiction_id>/auditboard/<audit_board_id>/status')
def jurisdiction_auditboard_status(jurisdiction_id, audit_board_id):
    pass

@app.route('/jurisdiction/<jurisdiction_id>/auditboard/<audit_board_id>/cvr/<cvr_id>')
def jurisdiction_auditboard_cvr(jurisdiction_id, audit_board_id, cvr_id):
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
