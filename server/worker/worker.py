import logging
import time

from server.database import db_session
from server.worker.tasks import run_new_tasks
from server.sentry import configure_sentry
from server.websession import cleanup_sessions

# We have to import all of the api so that the modules load and all of the task
# handlers get registered as background_tasks.
from server import api  # pylint: disable=unused-import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arlo.worker")


if __name__ == "__main__":
    logger.info("Worker starting up")
    logger.error("Test error log")
    print("level:", logger.level)
    print("effective level:", logger.getEffectiveLevel())
    print("Print worker starting up")
    configure_sentry()
    while True:
        run_new_tasks()
        cleanup_sessions()
        # Before sleeping, we need to commit the current transaction, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(2)
