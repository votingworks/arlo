import datetime
import uuid
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

from ...database import db_session
from ...models import File
from ...util.process_file import process_file


def test_success():
    file = File(
        id=str(uuid.uuid4()),
        name="Test File",
        contents="abcdefg",
        uploaded_at=datetime.datetime.utcnow(),
    )
    db_session.add(file)
    db_session.commit()

    def process():
        pass

    assert file.processing_started_at is None
    assert file.processing_completed_at is None
    assert file.processing_error is None

    process_file(db_session, file, process)

    assert isinstance(file.processing_started_at, datetime.datetime)
    assert isinstance(file.processing_completed_at, datetime.datetime)
    assert file.processing_error is None


def test_error():
    file = File(
        id=str(uuid.uuid4()),
        name="Test File",
        contents="abcdefg",
        uploaded_at=datetime.datetime.utcnow(),
    )
    db_session.add(file)
    db_session.commit()

    def process():
        raise Exception("NOPE")

    assert file.processing_started_at is None
    assert file.processing_completed_at is None
    assert file.processing_error is None

    try:
        process_file(db_session, file, process)
    except Exception as error:
        assert str(error) == "NOPE"

    assert isinstance(file.processing_started_at, datetime.datetime)
    assert isinstance(file.processing_completed_at, datetime.datetime)
    assert file.processing_error == "NOPE"


def test_session_stuck():
    file = File(
        id=str(uuid.uuid4()),
        name="Test File",
        contents="abcdefg",
        uploaded_at=datetime.datetime.utcnow(),
    )
    db_session.add(file)
    db_session.commit()

    def process():
        # We do something here that renders a db session unable to commit,
        # specifically trying to violate a db constraint. Note that we're not
        # using the models here because doing so makes sqlalchemy notice the
        # conflict before it even gets to the db.
        db_session.execute(
            insert(File.__table__).values(  # pylint: disable=no-member
                id=file.id,
                name="Test File2",
                contents="abcdefg",
                uploaded_at=datetime.datetime.utcnow(),
            )
        )

    try:
        process_file(db_session, file, process)
    except SQLAlchemyError:
        pass

    assert isinstance(file.processing_started_at, datetime.datetime)
    assert isinstance(file.processing_completed_at, datetime.datetime)
    assert file.processing_error
