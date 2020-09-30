from flask import Blueprint

api = Blueprint("api", __name__)

# pylint: disable=wrong-import-position,cyclic-import

# Single-jurisdiction flow routes
from . import routes

# Multi-jurisdiction flow routes
from . import election_settings
from . import contests
from . import jurisdictions
from . import standardized_contests
from . import rounds
from . import sample_sizes
from . import ballot_manifest
from . import batch_tallies
from . import cvrs
from . import audit_boards
from . import ballots
from . import batches
from . import offline_results
from . import reports
