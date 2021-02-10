release: alembic upgrade head
web: gunicorn server.app:app --preload
worker: python -m server.worker.bgcompute