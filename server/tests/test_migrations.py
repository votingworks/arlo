import pytest
from alembic.config import Config
from alembic import command
from ..db.setup import Base, engine

# Use the pytest-alembic plugin to test our migrations.
# More details on what is tested here:
# https://pytest-alembic.readthedocs.io/en/latest/quickstart.html#built-in-tests

# To configure the plugin, you have to override the two fixtures below.


@pytest.fixture
def alembic_config():
    # Tell pytest-alembic where to find our alembic migrations directory.
    return {"script_location": "server/migrations"}


@pytest.fixture
def alembic_engine():
    # Drop all the tables from our schema.
    Base.metadata.drop_all(bind=engine)
    # Alembic stores which version of the db inside an alembic_version table in
    # the db. So after running each test (which each run migrations) we need to
    # tell Alembic that we reset, which will cause it to reset that marker.
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "base")
    return engine


# Note: The plugin docs say you should run it via `pytest --test-alembic`, in
# which case the plugin appends some test cases to your test run. However, in
# order to override the fixtures, you need a conftest.py module within the
# directory where pytest is run (or at least, that's the only way I could get
# it to work). We work around this by importing the test cases directly, which
# seems to work fine.
# pylint: disable=wrong-import-position,unused-import,wrong-import-order
from pytest_alembic.tests import test_single_head_revision
from pytest_alembic.tests import test_upgrade
from pytest_alembic.tests import test_model_definitions_match_ddl
