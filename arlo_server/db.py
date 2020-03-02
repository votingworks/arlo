from flask_sqlalchemy import SQLAlchemy
from config import DATABASE_URL
from arlo_server.base import app

# database config
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
