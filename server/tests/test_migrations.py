from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database
from ..database import Base
from ..config import DATABASE_URL

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
    url = f"{DATABASE_URL}-migrations-{datetime.now(timezone.utc)}"
    if database_exists(url):
        drop_database(url)
    create_database(url)

    engine = create_engine(url)
    Base.metadata.drop_all(bind=engine)

    yield engine

    drop_database(url)


# Note: The plugin docs say you should run it via `pytest --test-alembic`, in
# which case the plugin appends some test cases to your test run. However, in
# order to override the fixtures, you need a conftest.py module within the
# directory where pytest is run (or at least, that's the only way I could get
# it to work). We work around this by importing the test cases directly, which
# seems to work fine.

from pytest_alembic.tests import test_single_head_revision  # noqa: E402, F401, F402
from pytest_alembic.tests import test_upgrade  # noqa: E402, F401, F402
from pytest_alembic.tests import test_model_definitions_match_ddl  # noqa: E402, F401, F402
