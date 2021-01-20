import uuid
import traceback
import json
import logging
from datetime import datetime
from typing import Optional, Callable, Dict

from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict
from ..config import FLASK_ENV


logger = logging.getLogger("arlo.worker")


task_dispatch: Dict[TaskName, Callable] = {}


# Decorator to register background task handlers.
def background_task(task_name: TaskName):
    def decorator(task_handler: Callable):
        task_dispatch[task_name] = task_handler
        return task_handler

    return decorator


def create_background_task(task_name: TaskName, payload: JSONDict) -> BackgroundTask:
    task = BackgroundTask(id=str(uuid.uuid4()), task_name=task_name, payload=payload)
    db_session.add(task)
    # In testing, we run the task immediately, since we'll only be doing small
    # tasks and we want to make sure they run in a thread-safe way (i.e. we
    # don't want tests to interfere with each other's background tasks when
    # running concurrently).
    if FLASK_ENV == "test":
        run_task(task)
    return task


class UserError(Exception):
    pass


# Currently, we assume that only one worker is consuming tasks at a time. There
# are no guards to prevent parallel workers from running the same task.
def run_task(task: BackgroundTask) -> bool:
    task_metadata = json.dumps(
        dict(id=task.id, task_name=task.task_name, payload=task.payload)
    )

    logger.info(f"TASK_START {task_metadata}")

    task.started_at = datetime.now(timezone.utc)

    # TODO what happens if the worker gets shut down right here?
    try:
        with db_session.begin_nested():
            task_handler = task_dispatch[TaskName(task.task_name)]
            assert task_handler, (
                f"No task handler registered for {task.task_name}."
                " Did you forget to use the @background_task decorator?"
            )

            task_handler(**dict(task.payload))

            task.completed_at = datetime.now(timezone.utc)

        db_session.commit()

        logger.info(f"TASK_COMPLETE {task_metadata}")

        return True
    except Exception as error:
        task.completed_at = datetime.now(timezone.utc)

        # Some errors stringify nicely, some don't (e.g. StopIteration) so we
        # have to format them.
        task.error = str(error) or str(
            traceback.format_exception(error.__class__, error, error.__traceback__)
        )

        db_session.commit()

        logger.info(f"TASK_ERROR {task_metadata}")

        if not isinstance(error, UserError):
            raise error
        return True


def run_new_tasks():
    for task in (
        BackgroundTask.query.filter_by(started_at=None)
        .order_by(BackgroundTask.created_at)
        .all()
    ):
        run_task(task)


def serialize_background_task(task: Optional[BackgroundTask]) -> Optional[JSONDict]:
    if task is None:
        return None

    if task.error:
        status = ProcessingStatus.ERRORED
    elif task.completed_at:
        status = ProcessingStatus.PROCESSED
    elif task.started_at:
        status = ProcessingStatus.PROCESSING
    else:
        status = ProcessingStatus.READY_TO_PROCESS

    return {
        "status": status,
        "startedAt": isoformat(task.started_at),
        "completedAt": isoformat(task.completed_at),
        "error": task.error,
    }
