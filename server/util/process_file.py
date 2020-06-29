import datetime
from typing import Any, Callable, Dict
from sqlalchemy import update
from sqlalchemy.orm.session import Session

from ..models import *  # pylint: disable=wildcard-import
from ..util.isoformat import isoformat


class UserError(Exception):
    pass


def process_file(session: Session, file: File, callback: Callable[[], None]) -> bool:
    if file.processing_started_at:
        return False

    # Claim this file by updating the `processing_started_at` timestamp in such
    # a way that it must not have been set before.
    processing_started_at = datetime.datetime.utcnow()
    result = session.execute(
        update(File.__table__)  # pylint: disable=no-member
        .where(File.id == file.id)
        .where(File.processing_started_at.is_(None))
        .values(processing_started_at=processing_started_at)
    )
    if result.rowcount == 0:
        return False

    # If we got this far, `file` is ours to process.
    try:
        callback()
        file.processing_started_at = processing_started_at
        file.processing_completed_at = datetime.datetime.utcnow()
        session.add(file)
        session.commit()
        return True
    except Exception as error:
        session.rollback()
        file.processing_started_at = processing_started_at
        file.processing_completed_at = datetime.datetime.utcnow()
        file.processing_error = str(error)
        session.add(file)
        session.commit()
        if not isinstance(error, UserError):
            raise error
        return True


def serialize_file(file: File) -> Dict[str, Any]:
    return {
        "name": file.name,
        "uploadedAt": isoformat(file.uploaded_at),
    }


def serialize_file_processing(file: File) -> Dict[str, Any]:
    if file.processing_error:
        status = ProcessingStatus.ERRORED
    elif file.processing_completed_at:
        status = ProcessingStatus.PROCESSED
    elif file.processing_started_at:
        status = ProcessingStatus.PROCESSING
    else:
        status = ProcessingStatus.READY_TO_PROCESS

    return {
        "status": status,
        "startedAt": isoformat(file.processing_started_at),
        "completedAt": isoformat(file.processing_completed_at),
        "error": file.processing_error,
    }
