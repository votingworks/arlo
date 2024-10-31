import uuid
import traceback
import logging
from inspect import signature
from datetime import datetime
from typing import Optional, Callable, Dict
from sqlalchemy.orm import Session
import sentry_sdk

from ..database import db_session, engine
from ..models import *  # pylint: disable=wildcard-import
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict
from .. import config

logger = logging.getLogger("arlo.worker")
# Something is setting the root logging level to WARNING in production, so we
# need to set this logger's level to INFO to ensure our info logs below are
# emitted.
logger.setLevel(logging.INFO)


class UserError(Exception):
    pass


task_dispatch: Dict[str, Callable] = {}


# Decorator to register background task handlers. We use the handler's function
# name as the key.
def background_task(task_handler: Callable):
    task_dispatch[task_handler.__name__] = task_handler
    assert (
        "election_id" in signature(task_handler).parameters
    ), f"Payload for task {task_handler.__name__} must include 'election_id' to easily identify all task logs for a single audit."
    return task_handler


def create_background_task(
    task_handler: Callable,
    payload: JSONDict,
    # Use the global db_session by default, but allow it to be overridden for testing.
    db_session=db_session,
) -> BackgroundTask:
    assert task_handler.__name__ in task_dispatch, (
        f"No task handler registered for {task_handler.__name__}."
        " Did you forget to use the @background_task decorator?"
    )
    task_parameters = set(signature(task_handler).parameters.keys()) - {
        "emit_progress",
        "db_session",
    }
    assert task_parameters == set(payload.keys()), (
        f"Payload for task {task_handler.__name__} must match the handler's parameters.\n"
        f"Expected: {task_parameters}\n"
        f"Got: {set(payload.keys())}\n"
    )

    task = BackgroundTask(
        id=str(uuid.uuid4()),
        task_name=task_handler.__name__,
        payload=payload,
        # Only allow one task per audit to run at a time. This ensures that
        # tasks won't try to access the same db resources at the same time.
        lock_key=f"election_id:{payload['election_id']}",
    )
    db_session.add(task)

    # For testing, we often prefer tasks to run immediately, instead of asynchronously.
    if config.RUN_BACKGROUND_TASKS_IMMEDIATELY:
        task.started_at = datetime.now(timezone.utc)
        db_session.commit()
        run_task(task, db_session)

    return task


def task_log_data(task: BackgroundTask) -> JSONDict:
    return dict(
        id=task.id,
        task_name=task.task_name,
        payload=task.payload,
        worker_id=task.worker_id,
    )


def emit_progress_for_task(task_id: str):
    progress_session = Session(engine)

    def emit_progress(work_progress: int, work_total: int):
        task = progress_session.query(BackgroundTask).get(task_id)
        task.work_progress = work_progress
        task.work_total = work_total
        progress_session.commit()

    return emit_progress


def run_task(task: BackgroundTask, db_session):
    task_handler = task_dispatch.get(task.task_name)
    assert task_handler, (
        f"No task handler registered for {task.task_name}."
        " Did you forget to use the @background_task decorator?"
    )

    logger.info(f"TASK_START {task_log_data(task)}")

    task_args = dict(task.payload)
    task_parameters = signature(task_handler).parameters
    # Inject emit_progress for handlers that want to record task progress
    if "emit_progress" in task_parameters:
        task_args["emit_progress"] = emit_progress_for_task(task.id)
    # For testing, allow the db_session to be injected into the task handler.
    if "db_session" in task_parameters:
        task_args["db_session"] = db_session

    try:
        task_handler(**task_args)

        task.completed_at = datetime.now(timezone.utc)

        db_session.commit()

        logger.info(f"TASK_COMPLETE {task_log_data(task)}")

    except Exception as error:
        db_session.rollback()

        task.completed_at = datetime.now(timezone.utc)

        # Some exceptions stringify nicely, some don't (e.g. StopIteration) so
        # we just print the exception class name.
        task.error = str(error) or str(error.__class__.__name__)

        db_session.commit()

        log_data = {
            **task_log_data(task),
            "error": task.error,
        }

        if isinstance(error, UserError):
            logger.info(f"TASK_USER_ERROR {log_data}")
        else:
            log_data["traceback"] = str(traceback.format_tb(error.__traceback__))
            logger.error(f"TASK_ERROR {log_data}")
            sentry_sdk.capture_exception(error)


def claim_next_task(worker_id: str, db_session) -> Optional[BackgroundTask]:
    # Use SELECT ... FOR UPDATE to lock all queued tasks, ensuring that only a
    # single worker can claim a single task at a time. This ensures that we get
    # an accurate view of which tasks are available to claim. If another worker has
    # already locked the queued task, this query will block (though it shouldn't
    # take long to claim a task, so this shouldn't cause problems).
    #
    # If new tasks are added after we lock the queued tasks, they won't be
    # accessible by this worker, but another worker also won't be able to claim
    # them (since it will also be trying to lock _all_ queued tasks, including
    # the ones we already locked).
    #
    # Importantly, this also ensures that we get a safe view of which lock_keys
    # are currently in use by in-progress tasks. If we're the only worker that
    # can claim a task right now, then no additional lock_keys can be locked. It
    # is possible for another worker to finish an in-progress task and release a
    # lock_key while we're running this query, but that's fine because even if
    # we don't see that change and wanted to claim that lock_key, we'll just fail
    # and try again later.
    #
    # Another approach to this would be to lock the entire table, but that would
    # also prevent in-progress tasks from completing.
    #
    # We don't actually need to load the queued tasks into the app, so we just
    # execute the query.
    (
        db_session.execute(
            db_session.query(BackgroundTask)
            .filter_by(started_at=None)
            .with_for_update()
            .with_entities(BackgroundTask.id)
        )
    )
    in_progress_task_lock_keys = (
        BackgroundTask.query.filter(BackgroundTask.started_at.isnot(None))
        .filter_by(completed_at=None)
        .with_entities(BackgroundTask.lock_key)
        .subquery()
    )
    task: Optional[BackgroundTask] = (
        db_session.query(BackgroundTask)
        .filter_by(started_at=None)
        # Only allow one task per lock key to run at a time.
        .filter(BackgroundTask.lock_key.notin_(in_progress_task_lock_keys))
        .order_by(BackgroundTask.created_at)
        .limit(1)
        .one_or_none()
    )
    if task:
        task.worker_id = worker_id
        task.started_at = datetime.now(timezone.utc)
        # Commit the transaction to release the lock before running the task,
        # allowing other workers to claim tasks in the meantime.
        db_session.commit()
    return task


def reset_task(task: BackgroundTask, db_session):
    # If a task got interrupted during processing, rollback any database changes
    # it made so far.
    db_session.rollback()

    # If the task is not in progress (e.g. already completed or already reset),
    # don't reset it.
    db_session.refresh(task)
    task_in_progress = task.started_at and not task.completed_at
    if not task_in_progress:
        return

    logger.info(f"TASK_RESET {task_log_data(task)}")
    task.worker_id = None
    task.started_at = None
    db_session.commit()


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

    json: JSONDict = {
        "status": status,
        "startedAt": isoformat(task.started_at),
        "completedAt": isoformat(task.completed_at),
        "error": task.error,
    }

    if task.work_total is not None:
        json["workProgress"] = task.work_progress
        json["workTotal"] = task.work_total

    return json
