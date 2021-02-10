release: alembic upgrade head
web: gunicorn server.app:app
worker: python -m server.worker.bgcompute