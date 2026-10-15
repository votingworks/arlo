#!/usr/bin/env bash

export FLASK_ENV=test
trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
cd ../..
uv run python -m scripts.cleardb
ORG_ID=`uv run python -m scripts.create-org "Cypress Test Org"`
uv run python -m scripts.create-admin $ORG_ID "audit-admin-cypress@example.com"