#!/usr/bin/env bash

export FLASK_ENV=test
trap 'kill 0' SIGINT SIGHUP
pushd ..
pipenv run python -m server.main &
pipenv run python -m server.bgcompute &
yarn --cwd client start &
yarn run wdio