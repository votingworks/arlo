#!/usr/bin/env bash

export FLASK_ENV=development
(trap 'kill 0' SIGINT SIGHUP; pipenv run python app.py & pipenv run python bgcompute.py & yarn --cwd arlo-client start)
