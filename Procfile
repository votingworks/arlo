release: if [[ $DATABASE_URL ]]; then alembic upgrade head; else echo "DATABASE_URL not set, skipping migrations"; fi
web: gunicorn server.app:app --preload
worker: python -m server.worker.worker
slack_worker: python -m server.activity_log.slack_worker
