from typing import Optional

from ..models import *  # pylint: disable=wildcard-import
from ..worker.tasks import serialize_background_task
from ..util.isoformat import isoformat
from ..util.jsonschema import JSONDict


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

    return serialize_background_task(file.task)
