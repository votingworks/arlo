#!/usr/bin/env bash

export ARLO_AUDITADMIN_AUTH0_BASE_URL=https://votingworks-noauth.herokuapp.com
export ARLO_JURISDICTIONADMIN_AUTH0_BASE_URL=https://votingworks-noauth.herokuapp.com

trap 'kill 0' SIGINT SIGHUP EXIT
./cypress/seed-test-db.sh
pushd ..
FLASK_ENV=test ./run-dev.sh &
popd
yarn run cypress run