from flask import Flask
from config import STATIC_FOLDER, SESSION_SECRET

app = Flask(__name__, static_folder=STATIC_FOLDER)
app.secret_key = SESSION_SECRET
