from flask import Flask
from config import STATIC_FOLDER, SESSION_SECRET, DATABASE_URL
from arlo_server.models import db

print("serving static files from " + STATIC_FOLDER)
app = Flask(__name__, static_folder=STATIC_FOLDER)
app.secret_key = SESSION_SECRET

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.app = app
db.init_app(app)

# The order of these imports is important as it defines route precedence.
# Be careful when re-ordering them.
import arlo_server.election_settings
import arlo_server.routes
import arlo_server.contests
import arlo_server.jurisdictions
import arlo_server.sample_sizes
import arlo_server.rounds
