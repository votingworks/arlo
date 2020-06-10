#!/usr/bin/env bash

export FLASK_ENV=development
(trap 'kill 0' SIGINT SIGHUP; pipenv run python -m server.main & pipenv run python -m server.bgcompute & yarn --cwd client start)
