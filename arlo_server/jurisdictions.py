from flask import jsonify

from arlo_server import app
from arlo_server.models import Election, Jurisdiction
from arlo_server.auth import with_election_access, UserType
from util.process_file import serialize_file, serialize_file_processing


def serialize_jurisdiction(db_jurisdiction: Jurisdiction) -> dict:
    return {
        "id": db_jurisdiction.id,
        "name": db_jurisdiction.name,
        "ballotManifest": {
            "file": serialize_file(db_jurisdiction.manifest_file)
            if db_jurisdiction.manifest_file
            else None,
            "processing": serialize_file_processing(db_jurisdiction.manifest_file)
            if db_jurisdiction.manifest_file
            else None,
            "numBallots": db_jurisdiction.manifest_num_ballots,
            "numBatches": db_jurisdiction.manifest_num_batches,
        },
    }


@app.route("/election/<election_id>/jurisdiction", methods=["GET"])
@with_election_access(UserType.AUDIT_ADMIN)
def list_jurisdictions(election: Election):
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election.id)
        .order_by(Jurisdiction.name)
        .all()
    )

    return jsonify([serialize_jurisdiction(j) for j in jurisdictions])
