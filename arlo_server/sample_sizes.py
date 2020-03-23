from flask import jsonify, request
from collections import defaultdict
import math
from werkzeug.exceptions import BadRequest
from typing import Dict

from arlo_server import app, db
from arlo_server.models import Election, Contest
from arlo_server.routes import require_audit_admin_for_organization
from audits import bravo, sampler_contest


@app.route("/election/<election_id>/sample-sizes", methods=["GET"])
def get_sample_sizes(election_id: str):
    election = Election.query.get_or_404(election_id)
    require_audit_admin_for_organization(election.organization_id)

    if not election.contests:
        raise BadRequest("Cannot compute sample sizes until contests are set")
    if not election.risk_limit:
        raise BadRequest("Cannot compute sample sizes until risk limit is set")

    # For now, we only support one targeted contest
    contest = next(c for c in election.contests if c.is_targeted)

    # Sum the audit results from previous rounds
    results_by_choice: Dict[str, int] = defaultdict(int)
    for result in contest.results:
        results_by_choice[result.contest_choice_id] += result.result
    results_so_far = {contest.id: results_by_choice}

    # Do the math!
    sample_sizes = bravo.get_sample_size(
        election.risk_limit / 100,
        sampler_contest.from_db_contest(contest),
        results_so_far,
    )

    # Convert the results into a slightly more regular format
    json_sizes = []
    for prob, size in sample_sizes.items():
        if prob == "asn":
            json_sizes.append(
                {
                    "type": "ASN",
                    "prob": round(size["prob"], 2),
                    "size": int(math.ceil(size["size"])),
                }
            )
        else:
            json_sizes.append(
                {"type": None, "prob": prob, "size": int(math.ceil(size)),}
            )

    return jsonify({"sampleSizes": json_sizes})
