#!/usr/bin/env bash

export FLASK_ENV=${FLASK_ENV:-development}
trap 'kill 0' SIGINT SIGHUP
cd "$(dirname "${BASH_SOURCE[0]}")"
PORT=8080 uv run python -m noauth &
uv run python -m server.main &
uv run python scripts/run-dev-worker.py &
pnpm --dir client start
