from typing import BinaryIO, Optional
import uuid
import logging
from datetime import datetime
from flask import request, jsonify, session
from werkzeug.exceptions import BadRequest, NotFound
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import api
from ..database import db_session, engine
from ..models import *  # pylint: disable=wildcard-import
from ..auth import restrict_access, UserType, get_loggedin_user, get_support_user
from ..worker.tasks import (
    UserError,
    background_task,
    create_background_task,
)
from ..util.file import (
    get_file_upload_url,
    get_standard_file_upload_request_params,
    retrieve_file,
    serialize_file,
    serialize_file_processing,
    timestamp_filename,
)
from ..util.csv_download import csv_response
from ..util.csv_parse import (
    CSVParseError,
    CSVValueType,
    CSVColumnType,
    parse_csv,
    validate_csv_mimetype,
)
from ..audit_math.suite import HybridPair
from . import contests
from . import cvrs
from .batch_tallies import reprocess_batch_tallies_file_if_uploaded
from ..activity_log.activity_log import UploadFile, activity_base, record_activity
from ..feature_flags import is_enabled_sample_extra_batches_by_counting_group


class CountingGroup(str, enum.Enum):
    ADVANCED_VOTING = "Advanced Voting"
    ADVANCE_VOTING = "Advance Voting"
    ELECTION_DAY = "Election Day"
    ELECTIONS_DAY = "Elections Day"
    ABSENTEE_BY_MAIL = "Absentee by Mail"
    PROVISIONAL = "Provisional"


logger = logging.getLogger("arlo")


CONTAINER = "Container"
TABULATOR = "Tabulator"
BATCH_NAME = "Batch Name"
NUMBER_OF_BALLOTS = "Number of Ballots"
CVR = "CVR"

BATCH_INVENTORY_WORKSHEET_UPLOADED_ERROR = 'You have uploaded a Batch Inventory Worksheet. Please upload a ballot manifest file exported from Step 4: "Download Audit Files".'


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

        is_counting_group_required = is_enabled_sample_extra_batches_by_counting_group(
            jurisdiction.election
        )

        columns = [
            CSVColumnType(
                CONTAINER,
                CSVValueType.TEXT,
                required_column=is_counting_group_required,
            ),
            CSVColumnType(
                TABULATOR,
                CSVValueType.TEXT,
                required_column=use_tabulator,
                unique=use_tabulator,
            ),
            CSVColumnType(BATCH_NAME, CSVValueType.TEXT, unique=True),
            CSVColumnType(NUMBER_OF_BALLOTS, CSVValueType.NUMBER),
        ]
        # Hybrid audits need a CVR column to tell us which batches have CVRS
        # (for which we use ballot comparison math) and which don't (for which
        # we use ballot polling math).
        if jurisdiction.election.audit_type == AuditType.HYBRID:
            columns.append(
                CSVColumnType(CVR, CSVValueType.YES_NO, required_column=True)
            )

        manifest_file = retrieve_file(jurisdiction.manifest_file.storage_path)
        validate_is_not_batch_inventory_worksheet(manifest_file)
        manifest_csv = parse_csv(manifest_file, columns)

        counting_group_allowlist = [item.value for item in CountingGroup]
        counting_group_allowset = set(counting_group_allowlist)

        num_batches = 0
        num_ballots = 0

        for row_index, row in enumerate(manifest_csv):
            counting_group = row.get(CONTAINER, None)
            if (
                is_counting_group_required
                and not counting_group in counting_group_allowset
            ):
                raise CSVParseError(
                    f"Invalid value for column \"Container\", row {row_index+2}: \"{counting_group}\". Use the Batch Audit File Preparation Tool to create your ballot manifest, or correct this value to one of the following: {', '.join(counting_group_allowlist)}."
                )

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
            cvrs.clear_cvr_contests_metadata(jurisdiction)
            cvrs.clear_cvr_ballots(jurisdiction.id)
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
        reprocess_batch_tallies_file_if_uploaded(
            jurisdiction,
            (UserType.JURISDICTION_ADMIN, jurisdiction_admin_email),
            support_user_email,
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


def is_batch_inventory_worksheet(first_line: bytes) -> bool:
    return first_line.decode("utf-8").strip() == "Batch Inventory Worksheet"


def validate_is_not_batch_inventory_worksheet(file: BinaryIO):
    first_line = file.readline()
    file.seek(0)
    if is_batch_inventory_worksheet(first_line):
        raise UserError(BATCH_INVENTORY_WORKSHEET_UPLOADED_ERROR)


def save_ballot_manifest_file(
    storage_path: str, file_name: str, jurisdiction: Jurisdiction
):
    jurisdiction.manifest_file = File(
        id=str(uuid.uuid4()),
        name=file_name,
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
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest/upload-url",
    methods=["GET"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def start_upload_for_ballot_manifest(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    file_type = request.args.get("fileType")
    if file_type is None:
        raise BadRequest("Missing expected query parameter: fileType")

    storage_path_prefix = (
        f"audits/{jurisdiction.election_id}/jurisdictions/{jurisdiction.id}"
    )
    filename = timestamp_filename("manifest", "csv")

    return jsonify(get_file_upload_url(storage_path_prefix, filename, file_type))


@api.route(
    "/election/<election_id>/jurisdiction/<jurisdiction_id>/ballot-manifest/upload-complete",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def complete_upload_for_ballot_manifest(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    (storage_path, filename, file_type) = get_standard_file_upload_request_params(
        request
    )
    validate_csv_mimetype(file_type)

    clear_ballot_manifest_file(jurisdiction)
    save_ballot_manifest_file(storage_path, filename, jurisdiction)
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
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
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,
):
    clear_ballot_manifest_file(jurisdiction)
    db_session.commit()
    return jsonify(status="ok")
