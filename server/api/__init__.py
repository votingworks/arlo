from flask import Blueprint

api = Blueprint("api", __name__)


from . import elections  # noqa: E402, F401
from . import election_settings  # noqa: E402, F401
from . import contests  # noqa: E402, F401
from . import jurisdictions  # noqa: E402, F401
from . import standardized_contests  # noqa: E402, F401
from . import rounds  # noqa: E402, F401
from . import sample_preview  # noqa: E402, F401
from . import sample_sizes  # noqa: E402, F401
from . import ballot_manifest  # noqa: E402, F401
from . import batch_tallies  # noqa: E402, F401
from . import batch_files  # noqa: E402, F401
from . import cvrs  # noqa: E402, F401
from . import audit_boards  # noqa: E402, F401
from . import ballots  # noqa: E402, F401
from . import batches  # noqa: E402, F401
from . import offline_results  # noqa: E402, F401
from . import full_hand_tally  # noqa: E402, F401
from . import reports  # noqa: E402, F401
from . import activity  # noqa: E402, F401
from . import support  # noqa: E402, F401
from . import batch_inventory  # noqa: E402, F401
from . import public  # noqa: E402, F401
from . import discrepancies  # noqa: E402, F401
