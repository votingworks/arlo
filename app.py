import os
from flask import Flask, send_from_directory, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='arlo-client/build/')

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./arlo.db'
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
@app.route('/admin/config', methods=["GET","POST"])
def audit_config():
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

@app.route('/admin/setup')
def audit_setup():
    pass

@app.route('/admin/randomseed')
def audit_randomseed():
    pass

# state of all the jurisdictions, round #, and contest status
@app.route('/admin/status')
def audit_status():
    pass

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
    app.run(use_reloader=True, port=3001, host='0.0.0.0', threaded=True)
