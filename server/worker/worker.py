import os
import signal
import sys
import time

from server.database import db_session
from server.worker.tasks import (
    claim_next_task,
    reset_task,
    run_task,
)
from server.sentry import configure_sentry
from server.websession import cleanup_sessions

# We have to import all of the api so that the modules load and all of the task
# handlers get registered as background_tasks.
from server import api  # pylint: disable=unused-import


def run_worker(worker_id: str):
    task = None

    # Heroku dynos are sent one or more SIGTERM signals when they are shut down,
    # then a SIGKILL if they don't exit after 30 seconds. If we're interrupted
    # in the middle of a task, reset it before exiting so it can be picked up by
    # another worker.
    def interrupt_handler(*_args):
        nonlocal task
        if task:
            reset_task(task)
            task = None
        sys.exit(1)

    signal.signal(signal.SIGTERM, interrupt_handler)
    # Also handle SIGINT for local development
    signal.signal(signal.SIGINT, interrupt_handler)

    while True:
        task = claim_next_task(worker_id)
        if task:
            run_task(task)
            # Ensure we don't reset the task on interrupt once it completes
            # successfully
            task = None

        # Unrelated, we use the same worker process to clean up expired web
        # sessions, since it's a convenient place to essentially run a cron job.
        cleanup_sessions(db_session)

        # Before sleeping, we need to commit the current transaction, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(2)


if __name__ == "__main__":
    worker_id = os.environ.get("HEROKU_DYNO_ID", str(os.getpid()))
    configure_sentry()
    run_worker(worker_id)
