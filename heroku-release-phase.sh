#!/usr/bin/env bash

if [[ $DATABASE_URL ]]; then
    alembic upgrade head
else
    echo "DATABASE_URL not set, skipping migrations"
fi