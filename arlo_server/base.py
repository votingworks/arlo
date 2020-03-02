from flask import Flask
from config import STATIC_FOLDER

app = Flask(__name__, static_folder=STATIC_FOLDER)
