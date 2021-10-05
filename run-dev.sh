#!/usr/bin/env bash

export ARLO_AUDITADMIN_AUTH0_BASE_URL=${ARLO_AUDITADMIN_AUTHO_BASE_URL:-http://localhost:8080}
export ARLO_SUPPORT_AUTH0_BASE_URL=${ARLO_SUPPORT_AUTHO_BASE_URL:-http://localhost:8080}
export FLASK_ENV=${FLASK_ENV:-development}
trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
PORT=8080 poetry run python -m noauth &
poetry run python -m server.main &
poetry run python -m server.worker.worker &
yarn --cwd client start
