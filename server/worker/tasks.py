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
from .. import config


logger = logging.getLogger("arlo.worker")


task_dispatch: Dict[str, Callable] = {}


# Decorator to register background task handlers. We use the handler's function name as the key.
def background_task(task_handler: Callable):
    task_dispatch[task_handler.__name__] = task_handler
    return task_handler


def create_background_task(task_handler: Callable, payload: JSONDict) -> BackgroundTask:
    assert task_handler.__name__ in task_dispatch, (
        f"No task handler registered for {task_handler.__name__}."
        " Did you forget to use the @background_task decorator?"
    )

    task = BackgroundTask(
        id=str(uuid.uuid4()), task_name=task_handler.__name__, payload=payload
    )
    db_session.add(task)

    if config.RUN_BACKGROUND_TASKS_IMMEDIATELY:
        run_task(task)

    return task


class UserError(Exception):
    pass


def task_log_data(task: BackgroundTask) -> str:
    return json.dumps(dict(id=task.id, task_name=task.task_name, payload=task.payload))


# Currently, we assume that only one worker is consuming tasks at a time. There
# are no guards to prevent parallel workers from running the same task.
def run_task(task: BackgroundTask) -> bool:
    task_handler = task_dispatch.get(task.task_name)
    assert task_handler, (
        f"No task handler registered for {task.task_name}."
        " Did you forget to use the @background_task decorator?"
    )

    logger.info(f"TASK_START {task_log_data(task)}")

    task.started_at = datetime.now(timezone.utc)

    db_session.commit()

    try:
        task_handler(**dict(task.payload))

        task.completed_at = datetime.now(timezone.utc)

        db_session.commit()

        logger.info(f"TASK_COMPLETE {task_log_data(task)}")

        return True
    except Exception as error:
        task.completed_at = datetime.now(timezone.utc)

        # Some errors stringify nicely, some don't (e.g. StopIteration) so we
        # have to format them.
        task.error = str(error) or str(
            traceback.format_exception(error.__class__, error, error.__traceback__)
        )

        db_session.commit()

        logger.info(f"TASK_ERROR {task_log_data(task)}")

        if not isinstance(error, UserError):
            raise error
        return True


def run_new_tasks():
    # Cleanup any tasks that failed to finish processing last time the worker was run
    stuck_tasks = BackgroundTask.query.filter(
        BackgroundTask.started_at is not None and BackgroundTask.completed_at is None
    ).all()
    for task in stuck_tasks:
        task.started_at = None
        logger.info(f"TASK_RESET {task_log_data(task)}")

    db_session.commit()

    # Find and run new tasks
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
