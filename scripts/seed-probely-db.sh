#!/usr/bin/env bash
BACKUP=${1:-latest.dump}
export FLASK_ENV=${FLASK_ENV:-development}
dropdb -U arlo arlo
createdb -U arlo arlo
pg_restore --verbose --clean --no-acl --no-owner -U arlo -d $DATABASE_URL $BACKUP
