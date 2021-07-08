#!/usr/bin/env bash

export FLASK_ENV=test
trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
cd ../..
poetry run python -m scripts.cleardb
ORG_ID=`poetry run python -m scripts.create-org "Cypress Test Org"`
poetry run python -m scripts.create-admin $ORG_ID "audit-admin-cypress@example.com"