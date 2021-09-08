import time

from server.database import db_session
from server.worker.tasks import run_new_tasks
from server.sentry import configure_sentry

if __name__ == "__main__":
    configure_sentry()
    while True:
        run_new_tasks()
        # Before sleeping, we need to commit the current transaction, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(2)
