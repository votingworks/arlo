#!/usr/bin/env bash

export FLASK_ENV=development
(trap 'kill 0' SIGINT SIGHUP; pipenv run python server/main.py & pipenv run python server/bgcompute.py & yarn --cwd client start)
