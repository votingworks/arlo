from typing import Optional
import uuid
import logging
from datetime import datetime
from flask import request, jsonify, Request, session
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import api
from ..database import db_session, engine
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType, get_loggedin_user, get_support_user
from ..worker.tasks import (
    background_task,
    create_background_task,
)
from ..util.file import (
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    store_file,
    timestamp_filename,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import (
    CSVValueType,
    CSVColumnType,
    parse_csv,
    validate_csv_mimetype,
)
from ..audit_math.suite import HybridPair
from . import contests
from . import cvrs
from .batch_tallies import (
    clear_batch_tallies_data,
    process_batch_tallies_file,
)
from ..activity_log.activity_log import UploadFile, activity_base, record_activity

logger = logging.getLogger("arlo")

CONTAINER = "Container"
TABULATOR = "Tabulator"
BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
CVR = "CVR"


def all_manifests_uploaded(contest: Contest):
    return all(
        jurisdiction.manifest_num_ballots is not None
        for jurisdiction in contest.jurisdictions
    )


def set_total_ballots_from_manifests(contest: Contest):
    if not all_manifests_uploaded(contest):
        return

    contest.total_ballots_cast = sum(
        jurisdiction.manifest_num_ballots for jurisdiction in contest.jurisdictions
    )


def hybrid_contest_total_ballots(contest: Contest) -> HybridPair:
    total_ballots = dict(
        Contest.query.filter_by(id=contest.id)
        .join(Contest.jurisdictions)
        .join(Batch)
        .group_by(Batch.has_cvrs)
        .values(Batch.has_cvrs, func.sum(Batch.num_ballots))
    )
    return HybridPair(
        cvr=total_ballots.get(True, 0), non_cvr=total_ballots.get(False, 0)
    )


def hybrid_jurisdiction_total_ballots(jurisdiction: Jurisdiction) -> HybridPair:
    total_ballots = dict(
        Batch.query.filter_by(jurisdiction_id=jurisdiction.id)
        .group_by(Batch.has_cvrs)
        .values(Batch.has_cvrs, func.sum(Batch.num_ballots))
    )
    return HybridPair(
        cvr=total_ballots.get(True, 0), non_cvr=total_ballots.get(False, 0)
    )


@background_task
def process_ballot_manifest_file(
    jurisdiction_id: str,
    jurisdiction_admin_email: str,
    support_user_email: Optional[str],
):
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)

    def process() -> None:
        # In ballot comparison and hybrid audits, each batch is uniquely
        # identified by (tabulator, batch name). For other types of audits, the
        # batch name is unique.
        use_tabulator = jurisdiction.election.audit_type in [
            AuditType.BALLOT_COMPARISON,
            AuditType.HYBRID,
        ]
        columns = [
            CSVColumnType(CONTAINER, CSVValueType.TEXT, required=False),
            CSVColumnType(
                TABULATOR,
                CSVValueType.TEXT,
                required=use_tabulator,
                unique=use_tabulator,
            ),
            CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True),
            CSVColumnType(NUMBER_OF_BALLOTS, CSVValueType.NUMBER),
        ]
        # Hybrid audits need a CVR column to tell us which batches have CVRS
        # (for which we use ballot comparison math) and which don't (for which
        # we use ballot polling math).
        if jurisdiction.election.audit_type == AuditType.HYBRID:
            columns.append(CSVColumnType(CVR, CSVValueType.YES_NO, required=True))

        manifest_file = retrieve_file(jurisdiction.manifest_file.storage_path)
        manifest_csv = parse_csv(manifest_file, columns)

        num_batches = 0
        num_ballots = 0
        for row in manifest_csv:
            batch = Batch(
                id=str(uuid.uuid4()),
                name=row[BATCH_NAME],
                jurisdiction_id=jurisdiction.id,
                num_ballots=row[NUMBER_OF_BALLOTS],
                container=row.get(CONTAINER, None),
                tabulator=row.get(TABULATOR, None),
                has_cvrs=row.get(CVR, None),
            )
            db_session.add(batch)
            num_batches += 1
            num_ballots += batch.num_ballots

        manifest_file.close()

        jurisdiction.manifest_num_ballots = num_ballots
        jurisdiction.manifest_num_batches = num_batches

        contests.set_contest_metadata(jurisdiction.election)

        # If CVR file already uploaded, try reprocessing it, since it depends on
        # batch names from the manifest
        if jurisdiction.cvr_file:
            cvrs.clear_cvr_data(jurisdiction)
            jurisdiction.cvr_file.task = create_background_task(
                cvrs.process_cvr_file,
                dict(
                    jurisdiction_id=jurisdiction.id,
                    jurisdiction_admin_email=jurisdiction_admin_email,
                    support_user_email=support_user_email,
                ),
            )

        # If batch tallies file already uploaded, try reprocessing it, since it
        # depends on batch names from the manifest
        if jurisdiction.batch_tallies_file:
            clear_batch_tallies_data(jurisdiction)
            jurisdiction.batch_tallies_file.task = create_background_task(
                process_batch_tallies_file,
                dict(
                    jurisdiction_id=jurisdiction.id,
                    jurisdiction_admin_email=jurisdiction_admin_email,
                    support_user_email=support_user_email,
                ),
            )

    error = None
    try:
        process()
    except Exception as exc:
        error = str(exc) or str(exc.__class__.__name__)
        raise exc
    finally:
        session = Session(engine)
        base = activity_base(jurisdiction.election)
        base.user_type = UserType.JURISDICTION_ADMIN
        base.user_key = jurisdiction_admin_email
        base.support_user_email = support_user_email
        record_activity(
            UploadFile(
                timestamp=jurisdiction.manifest_file.uploaded_at,
                base=base,
                jurisdiction_id=jurisdiction.id,
                jurisdiction_name=jurisdiction.name,
                file_type="ballot_manifest",
                error=error,
            ),
            session,
        )
        session.commit()


# Raises if invalid
def validate_ballot_manifest_upload(request: Request):
    if "manifest" not in request.files:
        raise BadRequest("Missing required file parameter 'manifest'")

    validate_csv_mimetype(request.files["manifest"])


def save_ballot_manifest_file(manifest, jurisdiction: Jurisdiction):
    storage_path = store_file(
        manifest.stream,
        f"audits/{jurisdiction.election_id}/jurisdictions/{jurisdiction.id}/"
        + timestamp_filename("manifest", "csv"),
    )
    jurisdiction.manifest_file = File(
        id=str(uuid.uuid4()),
        name=manifest.filename,
        storage_path=storage_path,
        uploaded_at=datetime.now(timezone.utc),
    )
    jurisdiction.manifest_file.task = create_background_task(
        process_ballot_manifest_file,
        dict(
            jurisdiction_id=jurisdiction.id,
            jurisdiction_admin_email=get_loggedin_user(session)[1],
            support_user_email=get_support_user(session),
        ),
    )


def clear_ballot_manifest_file(jurisdiction: Jurisdiction):
    jurisdiction.manifest_num_ballots = None
    jurisdiction.manifest_num_batches = None

    if jurisdiction.manifest_file_id:
        File.query.filter_by(id=jurisdiction.manifest_file_id).delete()
    Batch.query.filter_by(jurisdiction=jurisdiction).delete()


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["PUT"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def upload_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    validate_ballot_manifest_upload(request)
    clear_ballot_manifest_file(jurisdiction)
    save_ballot_manifest_file(request.files["manifest"], jurisdiction)
    db_session.commit()
    return jsonify(status="ok")


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def get_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction  # pylint: disable=unused-argument
):
    return jsonify(
        file=serialize_file(jurisdiction.manifest_file),
        processing=serialize_file_processing(jurisdiction.manifest_file),
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest/csv",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN])
def download_ballot_manifest_file(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    if not jurisdiction.manifest_file:
        return NotFound()

    return csv_response(
        retrieve_file(jurisdiction.manifest_file.storage_path),
        jurisdiction.manifest_file.name,
    )


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest",
    methods=["DELETE"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def clear_ballot_manifest(
    election: Election, jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    clear_ballot_manifest_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
