#!/usr/bin/env bash

trap 'kill 0' SIGINT SIGHUP EXIT
./cypress/seed-test-db.sh
pushd ..
FLASK_ENV=test ./run-dev.sh &
popd
yarn run cypress run