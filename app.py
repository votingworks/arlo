import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='arlo-client/build/')

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./arlo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import *

# get/set audit config
# state and jurisdictions[]
@app.route('/admin/config')
def audit_config():
    pass

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
        print(path)
        return send_from_directory(app.static_folder, path)
    else:
        print(path, "INDEX")
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(use_reloader=True, port=3001, threaded=True)
