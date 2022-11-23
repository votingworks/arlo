#!/usr/bin/env bash

echo "Attempting to run migrations"
if [[ $DATABASE_URL ]]; then
    alembic upgrade head

    # Reset the db if we're deploying the vuln scanning app
    if [[ $SCANNING_INSTANCE ]]; then
        env $FLASK_ENV python -m scripts.resetdb
    fi
else
    echo "DATABASE_URL not set, skipping migrations"
fi
