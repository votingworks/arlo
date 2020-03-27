#!/usr/bin/env bash

export FLASK_ENV=development
(trap 'kill 0' SIGINT SIGHUP; python3.7 -m pipenv run python app.py & python3.7 -m pipenv run python bgcompute.py & yarn --cwd arlo-client start)
