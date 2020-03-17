import datetime
from typing import Callable
from sqlalchemy import update
from sqlalchemy.orm.session import Session

from arlo_server.models import File


def process_file(session: Session, file: File, callback: Callable[[], None]) -> bool:
    if file.processing_started_at:
        return False

    # Claim this file by updating the `processing_started_at` timestamp in such
    # a way that it must not have been set before.
    file.processing_started_at = datetime.datetime.utcnow()
    result = session.execute(
        update(File.__table__)
        .where(File.id == file.id)
        .where(File.processing_started_at == None)
        .values(processing_started_at=file.processing_started_at)
    )
    if result.rowcount == 0:
        return False

    # If we got this far, `file` is ours to process.
    session.add(file)
    try:
        callback()
        file.processing_completed_at = datetime.datetime.utcnow()
        session.commit()
        return True
    except Exception as error:
        file.processing_completed_at = datetime.datetime.utcnow()
        file.processing_error = str(error)
        session.commit()
        raise error
