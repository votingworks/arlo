from multiprocessing import Manager, Process, current_process
import random
import signal
import sys
import time
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy import create_engine
from server.config import DATABASE_URL
from server.database import db_session, engine
from server.models import BackgroundTask
from server.worker.tasks import (
    background_task,
    claim_next_task,
    create_background_task,
    reset_task,
    run_task,
)

manager = Manager()
nums = manager.list()


def run_worker():
    name = current_process().name
    task = None

    def term_handler(*_args):
        print(f"Worker received SIGTERM: {name}")
        nonlocal task
        if task:
            reset_task(task)
        sys.exit(1)

    signal.signal(signal.SIGTERM, term_handler)

    engine = create_engine(DATABASE_URL)
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=True, bind=engine),
    )

    print(f"Running worker: {name}")
    while True:
        task = claim_next_task(db_session)
        if not task:
            break
        run_task(task, db_session)
        db_session.commit()

    print(f"Finished worker: {name}")
    db_session.close()
    engine.dispose()


@background_task
def count(num: int):
    time.sleep(random.randint(0, 3) / 10)
    nums.append(num)
    print(num)


if __name__ == "__main__":
    BackgroundTask.query.filter_by(task_name="count").delete()
    db_session.commit()

    print("starting tasks", BackgroundTask.query.filter_by(task_name="count").count())

    # Enqueue tasks
    for num in range(50):
        print(f"Enqueueing task {num}")
        create_background_task(count, dict(num=num))
    db_session.commit()
    db_session.close()
    engine.dispose()

    # Start two worker processes
    workers = [Process(target=run_worker) for _ in range(4)]
    for worker in workers:
        print(f"Starting worker: {worker.name}")
        worker.start()

    time.sleep(1)
    workers[0].terminate()
    time.sleep(1)
    workers[1].terminate()

    for worker in workers:
        worker.join()

    print(sorted(nums))
    duplicates = [n for n in nums if nums.count(n) > 1]
    print("duplicates:", duplicates)
