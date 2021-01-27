import pytest
import sqlalchemy

from .. import config
from ..models import *  # pylint: disable=wildcard-import
from .helpers import *  # pylint: disable=wildcard-import
from ..worker.tasks import (
    create_background_task,
    background_task,
    run_new_tasks,
    serialize_background_task,
    UserError,
)


@pytest.fixture(autouse=True)
def setup():
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = False
    yield
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = True


# Note: the tests in this file cannot be run in parallel, since the worker
# logic assumes only one worker is running at a time. We accomplish this by
# running them all as part of one test case, instead of registering them
# individually with pytest.
def test_background_task(caplog):
    task_happy_path(caplog)
    task_user_error(caplog)
    task_python_error(caplog)
    task_python_error_format(caplog)
    task_db_error(caplog)
    task_multiple_run_in_order()
    task_interrupted(caplog)


def task_happy_path(caplog):
    task_ran = False
    task_id = None
    test_payload = dict(arg2=2, arg1=1)  # Order shouldn't matter

    @background_task
    def happy_path(arg1, arg2):
        assert arg1 == 1
        assert arg2 == 2

        task = BackgroundTask.query.get(task_id)
        compare_json(
            serialize_background_task(task),
            {
                "status": "PROCESSING",
                "startedAt": assert_is_date,
                "completedAt": None,
                "error": None,
            },
        )

        nonlocal task_ran
        task_ran = True

    assert task_ran is False

    task = create_background_task(happy_path, test_payload)
    task_id = task.id

    compare_json(
        serialize_background_task(task),
        {
            "status": "READY_TO_PROCESS",
            "startedAt": None,
            "completedAt": None,
            "error": None,
        },
    )

    assert task_ran is False

    run_new_tasks()

    task = BackgroundTask.query.get(task_id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "PROCESSED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": None,
        },
    )

    assert task_ran is True

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task_id}', "
            "'task_name': 'happy_path',"
            f" 'payload': {{'arg2': 2, 'arg1': 1}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_COMPLETE {{'id': '{task_id}', "
            "'task_name': 'happy_path',"
            f" 'payload': {{'arg2': 2, 'arg1': 1}}}}"
        ),
    )


def task_user_error(caplog):
    @background_task
    def user_error():
        raise UserError("something went wrong")

    task = create_background_task(user_error, {})

    run_new_tasks()

    task = BackgroundTask.query.get(task.id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "ERRORED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": "something went wrong",
        },
    )

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task.id}', "
            "'task_name': 'user_error',"
            f" 'payload': {{}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_USER_ERROR {{'id': '{task.id}', "
            "'task_name': 'user_error',"
            f" 'payload': {{}},"
            " 'error': 'something went wrong'}"
        ),
    )


def task_python_error(caplog):
    @background_task
    def python_error():
        return [][1]

    task = create_background_task(python_error, {})

    with pytest.raises(IndexError):
        run_new_tasks()

    task = BackgroundTask.query.get(task.id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "ERRORED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": "list index out of range",
        },
    )

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task.id}', "
            "'task_name': 'python_error',"
            f" 'payload': {{}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'python_error',"
            f" 'payload': {{}},"
            " 'error': 'list index out of range', 'traceback':"
        ),
    )

    # Python error that doesn't stringify normally


def task_python_error_format(caplog):
    @background_task
    def error_format():
        return next(iter([]))

    task = create_background_task(error_format, {})

    with pytest.raises(StopIteration):
        run_new_tasks()

    task = BackgroundTask.query.get(task.id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "ERRORED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": "StopIteration",
        },
    )

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task.id}', "
            "'task_name': 'error_format',"
            f" 'payload': {{}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'error_format',"
            f" 'payload': {{}},"
            " 'error': 'StopIteration', 'traceback':"
        ),
    )


def task_db_error(caplog):
    @background_task
    def db_error():
        db_session.add(Election(id=1))

    task = create_background_task(db_error, {})

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        run_new_tasks()

    task = BackgroundTask.query.get(task.id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "ERRORED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": asserts_startswith(
                '(psycopg2.errors.NotNullViolation) null value in column "audit_name" violates not-null constraint'
            ),
        },
    )

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task.id}', "
            "'task_name': 'db_error',"
            f" 'payload': {{}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'db_error',"
            f" 'payload': {{}},"
            " 'error': '(psycopg2.errors.NotNullViolation) null value in column \"audit_name\" violates not-null constraint"
        ),
    )


def task_multiple_run_in_order():
    results = []

    @background_task
    def multiple(num):
        nonlocal results
        results.append(num)

    create_background_task(multiple, dict(num=1))
    create_background_task(multiple, dict(num=2))
    create_background_task(multiple, dict(num=3))

    run_new_tasks()

    assert results == [1, 2, 3]


def task_interrupted(caplog):
    results = []

    @background_task
    def interrupted(num):
        nonlocal results
        results.append(num)

    task1 = create_background_task(interrupted, dict(num=1))
    create_background_task(interrupted, dict(num=2))

    # Simulate that the worker got interrupted mid-task
    task1.started_at = datetime.now(timezone.utc)
    db_session.commit()

    run_new_tasks()

    assert results == [1, 2]

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_RESET {{'id': '{task1.id}', "
            "'task_name': 'interrupted',"
            f" 'payload': {{'num': 1}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task1.id}', "
            "'task_name': 'interrupted',"
            f" 'payload': {{'num': 1}}}}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_COMPLETE {{'id': '{task1.id}', "
            "'task_name': 'interrupted',"
            f" 'payload': {{'num': 1}}}}"
        ),
    )
