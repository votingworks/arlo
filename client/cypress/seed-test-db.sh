#!/usr/bin/env bash

export FLASK_ENV=test
trap 'kill 0' SIGINT SIGHUP
pushd ..
pipenv run python -m scripts.resetdb --skip-db-creation
ORG_ID=`pipenv run python -m scripts.create-org "Cypress Test Org"`
pipenv run python -m scripts.create-admin $ORG_ID "audit-admin-cypress@example.com"
popd