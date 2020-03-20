from flask import jsonify

from arlo_server import app, db
from arlo_server.routes import (
    get_election,
    require_audit_admin_for_organization,
    isoformat,
)
from arlo_server.models import Jurisdiction


def serialize_jurisdiction(db_jurisdiction: Jurisdiction) -> dict:
    return {
        "id": db_jurisdiction.id,
        "name": db_jurisdiction.name,
        "ballotManifest": {
            "filename": db_jurisdiction.manifest_file.name
            if db_jurisdiction.manifest_file
            else None,
            "numBallots": db_jurisdiction.manifest_num_ballots,
            "numBatches": db_jurisdiction.manifest_num_batches,
            "uploadedAt": isoformat(db_jurisdiction.manifest_file.uploaded_at)
            if db_jurisdiction.manifest_file
            else None,
        },
    }


@app.route("/election/<election_id>/jurisdiction", methods=["GET"])
def list_jurisdictions(election_id: str = None):
    election = get_election(election_id)
    require_audit_admin_for_organization(election.organization_id)

    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election.id)
        .order_by(Jurisdiction.name)
        .all()
    )

    return jsonify([serialize_jurisdiction(j) for j in jurisdictions])
