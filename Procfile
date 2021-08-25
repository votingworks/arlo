release: alembic upgrade head
web: gunicorn server.app:app --preload
worker: python -m server.worker.worker
slack_worker: python -m server.activity_log.slack_worker