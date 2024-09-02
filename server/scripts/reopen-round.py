# pylint: disable=invalid-name
import sys

from server.models import Election
from server.database import db_session
from server.api.rounds import get_current_round

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.reopen-round <election_id>")
        sys.exit(1)

    election_id = sys.argv[1]
    election = Election.query.get(election_id)
    if not election:
        print("Audit not found")
        sys.exit(1)

    print(f"Audit: {election.audit_name}")

    round = get_current_round(election)

    if not round:
        print("Audit has not started yet")
        sys.exit(1)

    if not round.ended_at:
        print("Round is in progress")
        sys.exit(1)

    if input(f"Are you sure you want to reopen round {round.round_num}? [y/n] ") != "y":
        sys.exit()

    print("Reopening round")
    round.ended_at = None
    for round_contest in round.round_contests:
        round_contest.results = []
        round_contest.end_p_value = None
        round_contest.is_complete = None
    db_session.commit()
