import pytest
from .. import config

from ..models import *  # pylint: disable=wildcard-import
from .helpers import *  # pylint: disable=wildcard-import
from ..worker import tasks
from ..worker.tasks import (
    create_background_task,
    background_task,
    run_new_tasks,
    serialize_background_task,
)


@pytest.fixture(autouse=True)
def setup():
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = False
    yield
    config.RUN_BACKGROUND_TASKS_IMMEDIATELY = True


def test_task_happy_path():
    task_ran = False
    task_id = None
    test_payload = dict(b=2, a=1)  # Order shouldn't matter

    @background_task
    def do_the_thing(a, b):
        assert a == 1
        assert b == 2

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

    task = create_background_task(do_the_thing, test_payload)
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


# TODO
# - test exceptions (UserError, python error, db error)
# - test interrupt and cleanup
