#!/usr/bin/env bash

trap 'kill 0' SIGINT SIGHUP
pushd ..
FLASK_ENV=test ./run-dev.sh &
popd
yarn run wdio