release: ./heroku-release-phase.sh
# gunicorn runs multiple worker processes based on the WEB_CONCURRENCY
# environment variable (set by Heroku automatically based on dyno size).
# https://devcenter.heroku.com/articles/python-concurrency#common-runtime
# At the time of writing, we use Standard-2x dynos, which results in 4 workers.
# To tame slow memory leakage that we've observed but haven't solved, we
# configure gunicorn to restart each worker after a certain number of requests
# (with some random jitter). This threshold was set by observing how long it
# took for memory to rise to an unacceptable level during peak traffic, then
# counting the number of requests in that internval and dividing by the number
# of workers.
web: gunicorn server.app:app --preload --max-requests 1000 --max-requests-jitter 50
worker: python -m server.worker.worker
slack_worker: python -m server.activity_log.slack_worker
