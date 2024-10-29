import logging
import multiprocessing
import random
import time
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
    claim_next_task,
    create_background_task,
    background_task,
    reset_task,
    run_task,
    serialize_background_task,
    UserError,
)
from ..worker.worker import run_worker


# We give each test case its own database to work with so there is no
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

    run_task(claim_next_task("test_worker", db_session), db_session)

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
            f" 'payload': {{'arg2': 2, 'arg1': 1}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_COMPLETE {{'id': '{task_id}', "
            "'task_name': 'happy_path',"
            f" 'payload': {{'arg2': 2, 'arg1': 1}},"
            " 'worker_id': 'test_worker'}"
        ),
    )


def test_task_user_error(caplog, db_session):
    @background_task
    def user_error():
        raise UserError("something went wrong")

    task = create_background_task(user_error, {}, db_session)

    run_task(claim_next_task("test_worker", db_session), db_session)

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
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_USER_ERROR {{'id': '{task.id}', "
            "'task_name': 'user_error',"
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker',"
            " 'error': 'something went wrong'}"
        ),
    )


@patch("sentry_sdk.capture_exception", auto_spec=True)
def test_task_python_error(capture_exception, caplog, db_session):
    @background_task
    def python_error():
        return [][1]  # pylint: disable=potential-index-error

    task = create_background_task(python_error, {}, db_session)

    run_task(claim_next_task("test_worker", db_session), db_session)

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
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'python_error',"
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker',"
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

    run_task(claim_next_task("test_worker", db_session), db_session)

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
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'error_format',"
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker',"
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

    run_task(claim_next_task("test_worker", db_session), db_session)

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
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.ERROR,
        (
            f"TASK_ERROR {{'id': '{task.id}', "
            "'task_name': 'db_error',"
            f" 'payload': {{}},"
            " 'worker_id': 'test_worker',"
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

    run_task(claim_next_task("test_worker", db_session), db_session)
    run_task(claim_next_task("test_worker", db_session), db_session)
    run_task(claim_next_task("test_worker", db_session), db_session)

    assert results == [1, 2, 3]


def test_task_interrupted(caplog, db_session):
    db_session.execute(
        """
        CREATE TABLE IF NOT EXISTS task_to_interrupt_results (
            num INT,
            inserted_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    db_session.execute("TRUNCATE TABLE task_to_interrupt_results")

    @background_task
    def task_to_interrupt(num):
        db_session.execute(
            "INSERT INTO task_to_interrupt_results (num) VALUES (:num)", dict(num=num)
        )

    task1 = create_background_task(task_to_interrupt, dict(num=1), db_session)
    task2 = create_background_task(task_to_interrupt, dict(num=2), db_session)

    # Simulate that the worker got interrupted mid-task
    claim_next_task("test_worker", db_session)
    db_session.commit()
    task_to_interrupt(num=1)  # Simulate starting the task before interruption
    reset_task(task1, db_session)

    # Try resetting a task that's already been reset - this should be a no-op
    reset_task(task1, db_session)

    # Continue running tasks
    run_task(claim_next_task("test_worker", db_session), db_session)
    run_task(claim_next_task("test_worker", db_session), db_session)
    # Ensure resetting didn't duplicate the task
    assert claim_next_task("test_worker", db_session) is None

    # Try resetting a task that's already completed
    reset_task(task2, db_session)
    db_session.commit()
    assert claim_next_task("test_worker", db_session) is None

    results = [
        num
        for num, in db_session.execute(
            "SELECT num FROM task_to_interrupt_results ORDER BY inserted_at"
        ).fetchall()
    ]
    assert results == [1, 2]

    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_RESET {{'id': '{task1.id}', "
            "'task_name': 'task_to_interrupt',"
            f" 'payload': {{'num': 1}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_START {{'id': '{task1.id}', "
            "'task_name': 'task_to_interrupt',"
            f" 'payload': {{'num': 1}},"
            " 'worker_id': 'test_worker'}"
        ),
    )
    assert find_log(
        caplog,
        logging.INFO,
        (
            f"TASK_COMPLETE {{'id': '{task1.id}', "
            "'task_name': 'task_to_interrupt',"
            f" 'payload': {{'num': 1}},"
            " 'worker_id': 'test_worker'}"
        ),
    )


def test_multiple_workers(db_session):
    context = multiprocessing.get_context()
    num_tasks = 40
    num_workers = 4
    expected_results = list(range(num_tasks))

    db_session.execute("CREATE TABLE IF NOT EXISTS count_results (num INT)")
    db_session.execute("TRUNCATE TABLE count_results")
    db_session.commit()

    @background_task
    def count(db_session, num: int):
        time.sleep(random.randint(0, 2) / 10)
        db_session.execute(
            "INSERT INTO count_results (num) VALUES (:num)", dict(num=num)
        )

    # Enqueue tasks
    for num in expected_results:
        create_background_task(count, dict(num=num), db_session)
    db_session.commit()

    db_url = db_session.bind.url

    def run_test_worker():
        engine = sqlalchemy.create_engine(db_url)
        db_session = scoped_session(
            sessionmaker(autocommit=False, autoflush=True, bind=engine)
        )
        name = context.current_process().name
        run_worker(
            name, db_session, pause_between_tasks_seconds=random.randint(0, 3) / 10
        )

    # Start worker processes. This simulates how workers are run in production -
    # each one in its own process.
    workers = [context.Process(target=run_test_worker) for _ in range(num_workers)]
    for worker in workers:
        worker.start()

    def num_completed_tasks():
        return (
            db_session.query(BackgroundTask)
            .filter_by(task_name="count")
            .filter(BackgroundTask.completed_at.isnot(None))
            .count()
        )

    while num_completed_tasks() < num_tasks / 2:
        time.sleep(0.1)

    # Terminate some workers to make sure their tasks are reset and picked up by others
    workers[0].terminate()
    workers[1].terminate()

    while num_completed_tasks() < num_tasks:
        time.sleep(0.1)

    for worker in workers:
        worker.terminate()

    expected_sorted_results = list(range(num_tasks))
    results = [
        num for num, in db_session.execute("SELECT num FROM count_results").fetchall()
    ]
    # Each task should have run exactly once
    assert sorted(results) == expected_sorted_results
