#!/usr/bin/env bash

export FLASK_ENV=${FLASK_ENV:-development}
trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
pipenv run python -m server.main &
pipenv run python -m server.worker.bgcompute &
yarn --cwd client start
