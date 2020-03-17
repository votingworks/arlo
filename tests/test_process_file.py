import datetime
import pytest
import uuid
from typing import Optional

import arlo_server
from arlo_server.models import File
from util.process_file import process_file


@pytest.fixture
def db():
    with arlo_server.app.app_context():
        arlo_server.db.drop_all()
        arlo_server.db.create_all()

    yield arlo_server.db

    arlo_server.db.session.commit()


def test_success(db):
    file = File(
        id=str(uuid.uuid4()),
        name="Test File",
        contents="abcdefg",
        uploaded_at=datetime.datetime.utcnow(),
    )
    db.session.add(file)
    db.session.commit()

    while_processing_started_at: Optional[datetime.datetime] = None
    while_processing_completed_at: Optional[datetime.datetime] = None
    while_processing_error: Optional[str] = None

    def process():
        nonlocal while_processing_started_at
        nonlocal while_processing_completed_at
        nonlocal while_processing_error

        while_processing_started_at = file.processing_started_at
        while_processing_completed_at = file.processing_completed_at
        while_processing_error = file.processing_error

    assert file.processing_started_at == None
    assert file.processing_completed_at == None
    assert file.processing_error == None

    process_file(db.session, file, process)

    assert isinstance(while_processing_started_at, datetime.datetime)
    assert while_processing_completed_at == None
    assert while_processing_error == None

    assert isinstance(file.processing_started_at, datetime.datetime)
    assert isinstance(file.processing_completed_at, datetime.datetime)
    assert file.processing_error == None


def test_error(db):
    file = File(
        id=str(uuid.uuid4()),
        name="Test File",
        contents="abcdefg",
        uploaded_at=datetime.datetime.utcnow(),
    )
    db.session.add(file)
    db.session.commit()

    while_processing_started_at: Optional[datetime.datetime] = None
    while_processing_completed_at: Optional[datetime.datetime] = None
    while_processing_error: Optional[str] = None

    def process():
        nonlocal while_processing_started_at
        nonlocal while_processing_completed_at
        nonlocal while_processing_error

        while_processing_started_at = file.processing_started_at
        while_processing_completed_at = file.processing_completed_at
        while_processing_error = file.processing_error

        raise Exception("NOPE")

    assert file.processing_started_at == None
    assert file.processing_completed_at == None
    assert file.processing_error == None

    try:
        process_file(db.session, file, process)
    except Exception as error:
        assert str(error) == "NOPE"

    assert isinstance(while_processing_started_at, datetime.datetime)
    assert while_processing_completed_at == None
    assert while_processing_error == None

    assert isinstance(file.processing_started_at, datetime.datetime)
    assert isinstance(file.processing_completed_at, datetime.datetime)
    assert file.processing_error == "NOPE"
