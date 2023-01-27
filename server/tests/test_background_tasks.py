from datetime import datetime
import logging
from unittest.mock import patch
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import create_database, drop_database
import pytest

from .. import config
from ..models import *  # pylint: disable=wildcard-import
from ..database import init_db
from .helpers import (
    compare_json,
    assert_is_date,
    asserts_startswith,
    find_log,
)
from ..worker.tasks import (
    create_background_task,
    background_task,
    serialize_background_task,
    UserError,
    run_new_tasks,
)


# Since the worker code assumes that only one worker is running at a time, we
# give each test case with its own database to work with so there is no
# interference with tests running concurrently (both among tests in this file
# and with the other tests).
@pytest.fixture
def db_session(request):
    url = f"{config.DATABASE_URL}-{request.node.name}"
    create_database(url)
    engine = sqlalchemy.create_engine(url)
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=True, bind=engine)
    )
    init_db(engine)

    yield db_session

    db_session.close()
    drop_database(url)


@pytest.fixture(autouse=True)
def setup():
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = False
    yield
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = True


def test_task_happy_path(caplog, db_session):
    task_ran = False
    task_id = None
    test_payload = dict(arg2=2, arg1=1)  # Order shouldn't matter

    @background_task
    def happy_path(arg1, arg2):
        assert arg1 == 1
        assert arg2 == 2

        task = db_session.query(BackgroundTask).get(task_id)
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

    assert serialize_background_task(None) is None

    task = create_background_task(happy_path, test_payload, db_session)
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

    run_new_tasks(db_session)

    task = db_session.query(BackgroundTask).get(task_id)
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


def test_task_user_error(caplog, db_session):
    @background_task
    def user_error():
        raise UserError("something went wrong")

    task = create_background_task(user_error, {}, db_session)

    run_new_tasks(db_session)

    task = db_session.query(BackgroundTask).get(task.id)
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


@patch("sentry_sdk.capture_exception", auto_spec=True)
def test_task_python_error(capture_exception, caplog, db_session):
    @background_task
    def python_error():
        return [][1]

    task = create_background_task(python_error, {}, db_session)

    run_new_tasks(db_session)

    task = db_session.query(BackgroundTask).get(task.id)
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

    capture_exception.assert_called_once()
    assert isinstance(capture_exception.call_args[0][0], IndexError)


@patch("sentry_sdk.capture_exception", auto_spec=True)
def test_task_python_error_format(capture_exception, caplog, db_session):
    @background_task
    def error_format():
        return next(iter([]))

    task = create_background_task(error_format, {}, db_session)

    run_new_tasks(db_session)

    task = db_session.query(BackgroundTask).get(task.id)
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

    capture_exception.assert_called_once()
    assert isinstance(capture_exception.call_args[0][0], StopIteration)


@patch("sentry_sdk.capture_exception", auto_spec=True)
def test_task_db_error(capture_exception, caplog, db_session):
    @background_task
    def db_error():
        db_session.add(Election(id=1))

    task = create_background_task(db_error, {}, db_session)

    run_new_tasks(db_session)

    task = db_session.query(BackgroundTask).get(task.id)
    compare_json(
        serialize_background_task(task),
        {
            "status": "ERRORED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": asserts_startswith(
                '(psycopg2.errors.NotNullViolation) null value in column "audit_name"'
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
            " 'error': '(psycopg2.errors.NotNullViolation) null value in column \"audit_name\""
        ),
    )

    capture_exception.assert_called_once()
    assert isinstance(capture_exception.call_args[0][0], sqlalchemy.exc.IntegrityError)


def test_task_multiple_run_in_order(db_session):
    results = []

    @background_task
    def multiple(num):
        nonlocal results
        results.append(num)

    create_background_task(multiple, dict(num=1), db_session)
    create_background_task(multiple, dict(num=2), db_session)
    create_background_task(multiple, dict(num=3), db_session)

    run_new_tasks(db_session)

    assert results == [1, 2, 3]


def test_task_interrupted(caplog, db_session):
    results = []

    @background_task
    def interrupted(num):
        nonlocal results
        results.append(num)

    task1 = create_background_task(interrupted, dict(num=1), db_session)
    create_background_task(interrupted, dict(num=2), db_session)

    # Simulate that the worker got interrupted mid-task
    task1.started_at = datetime.now(timezone.utc)
    db_session.commit()

    run_new_tasks(db_session)

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
