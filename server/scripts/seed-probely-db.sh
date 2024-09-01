#!/usr/bin/env bash
BACKUP=${1:-latest.dump}
python -m scripts.resetdb --skip-db-creation
pg_restore --verbose --clean --no-acl --no-owner -U arlo -d $DATABASE_URL $BACKUP
