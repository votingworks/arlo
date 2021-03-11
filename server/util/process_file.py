import datetime
import traceback
from typing import Callable, Optional
from sqlalchemy import update
from sqlalchemy.orm.session import Session

from ..models import *  # pylint: disable=wildcard-import
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict


class UserError(Exception):
    pass


def process_file(session: Session, file: File, callback: Callable[[], None]) -> bool:
    if file.processing_started_at:
        return False

    # Claim this file by updating the `processing_started_at` timestamp in such
    # a way that it must not have been set before.
    processing_started_at = datetime.datetime.now(timezone.utc)
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
        session.begin_nested()
        callback()
        file.processing_started_at = processing_started_at
        file.processing_completed_at = datetime.datetime.now(timezone.utc)
        session.add(file)
        session.commit()
        return True
    except Exception as error:
        session.rollback()
        file.processing_started_at = processing_started_at
        file.processing_completed_at = datetime.datetime.now(timezone.utc)
        # Some errors stringify nicely, some don't (e.g. StopIteration) so we
        # have to format them.
        file.processing_error = str(error) or str(
            traceback.format_exception(error.__class__, error, error.__traceback__)
        )
        if not isinstance(error, UserError):
            raise error
        return True


def serialize_file(file: Optional[File]) -> Optional[JSONDict]:
    if file is None:
        return None

    return {
        "name": file.name,
        "uploadedAt": isoformat(file.uploaded_at),
    }


def serialize_file_processing(file: Optional[File]) -> Optional[JSONDict]:
    if file is None:
        return None

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
