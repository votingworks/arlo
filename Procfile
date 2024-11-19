release: ./heroku-release-phase.sh
web: gunicorn server.app:app --preload --max-requests 5000 --max-requests-jitter 20
worker: python -m server.worker.worker
slack_worker: python -m server.activity_log.slack_worker
