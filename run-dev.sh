#!/usr/bin/env bash

read -p "Do you want to initialize environment variables?: (y/n) " input
if [[ $(tr '[:upper:]' '[:lower:]' <<< "$input") == "y" || $(tr '[:upper:]' '[:lower:]' <<< "$input") == "yes" ]]
then
    echo "Initializing environment variables:"
    export ARLO_AUDITADMIN_AUTH0_BASE_URL=${ARLO_AUDITADMIN_AUTHO_BASE_URL:-http://localhost:8080}
    export ARLO_AUDITADMIN_AUTH0_CLIENT_ID="test"
    export ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET="secret"
    export ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_ID="test"
    export ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_SECRET="secret"
    export ARLO_SUPPORT_AUTH0_BASE_URL=${ARLO_SUPPORT_AUTHO_BASE_URL:-http://localhost:8080}
    export ARLO_SUPPORT_AUTH0_CLIENT_ID="test"
    export ARLO_SUPPORT_AUTH0_CLIENT_SECRET="secret"
    export ARLO_SESSION_SECRET="secret"
    export ARLO_HTTP_ORIGIN="http://localhost:3000"
    export FLASK_ENV=${FLASK_ENV:-development}
fi

read -p "Do you want to seed DB for testing?: (y/n) " input
if [[ $(tr '[:upper:]' '[:lower:]' <<< "$input") == "y" || $(tr '[:upper:]' '[:lower:]' <<< "$input") == "yes" ]]
then
    echo "Initializing Organization and Audit Admin:"
    poetry run python -m scripts.cleardb
    ORG_ID=`poetry run python -m scripts.create-org "Test Organization"`
    poetry run python -m scripts.create-admin $ORG_ID "audit-admin@example.com"
fi

trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
PORT=8080 poetry run python -m noauth &
poetry run python -m server.main &
poetry run python -m server.worker.worker &
yarn --cwd client start
