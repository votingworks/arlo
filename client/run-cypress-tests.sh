#!/usr/bin/env bash

export ARLO_SMTP_HOST=localhost
export ARLO_SMTP_PORT=1025
export ARLO_SMTP_USERNAME=cypress-smtp-username
export ARLO_SMTP_PASSWORD=cypress-smtp-password

trap 'kill 0' SIGINT SIGHUP EXIT
cd "$(dirname "${BASH_SOURCE[0]}")"
FLASK_ENV=test ../run-dev.sh &
yarn run cypress run --browser chrome