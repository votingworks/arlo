#!/usr/bin/env bash

export ARLO_SMTP_HOST=localhost
export ARLO_SMTP_PORT=1025
export ARLO_SMTP_USERNAME=cypress-smtp-username
export ARLO_SMTP_PASSWORD=cypress-smtp-password
if [[ -n $AWS_ACCESS_KEY_ID ]] && [[ -n $AWS_SECRET_ACCESS_KEY ]]
then
    export ARLO_FILE_UPLOAD_STORAGE_PATH=s3://arlo-file-uploads-dev
fi

trap 'kill 0' SIGINT SIGHUP EXIT
cd "$(dirname "${BASH_SOURCE[0]}")"
FLASK_ENV=test ../run-dev.sh &
yarn run cypress run --browser chrome