#!/usr/bin/env bash

trap 'kill 0' SIGINT SIGHUP EXIT
pushd ..
FLASK_ENV=test ./run-dev.sh &
popd
yarn run wdio