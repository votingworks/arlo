# pylint: disable=invalid-name
import sys

from server.models import Election
from server.database import db_session
from server.api.shared import get_current_round, is_round_complete
from server.api.rounds import end_round

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.end-round <election_id>")
        sys.exit(1)

    election_id = sys.argv[1]
    election = Election.query.get(election_id)
    if not election:
        print("Audit not found")
        sys.exit(1)

    round = get_current_round(election)

    if not round:
        print("Audit has not started yet")
        sys.exit(1)

    if not is_round_complete(election, round):
        print("Round is not complete")
        sys.exit(1)

    if input(f"Are you sure you want to end round {round.round_num}? [y/n] ") != "y":
        sys.exit()

    print("Ending round")
    end_round(election, round)
    db_session.commit()
