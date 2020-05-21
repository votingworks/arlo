import json
import pytest
from flask.testing import FlaskClient

from tests.helpers import (
    compare_json,
    assert_is_id,
    assert_is_date,
    assert_is_passphrase,
    create_election,
)
from tests.test_app import setup_whole_audit
from util.process_file import ProcessingStatus


@pytest.fixture()
def election_id(client: FlaskClient) -> str:
    return create_election(client, is_multi_jurisdiction=False)


def test_audit_status(client, election_id):
    (
        _url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        _jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        _num_ballots,
    ) = setup_whole_audit(client, election_id, "Audit Status Test", 10, "1234567890")

    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)

    compare_json(
        status,
        {
            "contests": [
                {
                    "choices": [
                        {
                            "id": candidate_id_1,
                            "name": "candidate 1",
                            "numVotes": 48121,
                        },
                        {
                            "id": candidate_id_2,
                            "name": "candidate 2",
                            "numVotes": 38026,
                        },
                    ],
                    "id": contest_id,
                    "isTargeted": True,
                    "name": "contest 1",
                    "numWinners": 1,
                    "totalBallotsCast": 86147,
                    "votesAllowed": 1,
                }
            ],
            "frozenAt": assert_is_date,
            "isMultiJurisdiction": False,
            "jurisdictions": [
                {
                    "auditBoards": [
                        {
                            "id": audit_board_id_1,
                            "members": [
                                {"affiliation": "REP", "name": "Joe Schmo"},
                                {"affiliation": "", "name": "Jane Plain"},
                            ],
                            "name": "Audit Board #1",
                            "passphrase": assert_is_passphrase,
                        },
                        {
                            "id": audit_board_id_2,
                            "members": [],
                            "name": "audit board #2",
                            "passphrase": assert_is_passphrase,
                        },
                    ],
                    "ballotManifest": {
                        "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
                        "processing": {
                            "status": ProcessingStatus.PROCESSED,
                            "startedAt": assert_is_date,
                            "completedAt": assert_is_date,
                            "error": None,
                        },
                        "numBallots": 86147,
                        "numBatches": 484,
                        "filename": "manifest.csv",
                        "uploadedAt": assert_is_date,
                    },
                    "batches": lambda x: x,  # pass
                    "contests": [contest_id],
                    "id": assert_is_id,
                    "name": "adams county",
                }
            ],
            "name": "Audit Status Test",
            "online": False,
            "organizationId": None,
            "randomSeed": "1234567890",
            "riskLimit": 10,
            "rounds": [
                {
                    "contests": [
                        {
                            "endMeasurements": {"isComplete": None, "pvalue": None},
                            "id": contest_id,
                            "results": {},
                            "sampleSize": 1035,
                            "sampleSizeOptions": [
                                {"prob": 0.51, "size": 343, "type": "ASN"},
                                {"prob": 0.7, "size": 542, "type": None},
                                {"prob": 0.8, "size": 718, "type": None},
                                {"prob": 0.9, "size": 1035, "type": None},
                            ],
                        }
                    ],
                    "endedAt": None,
                    "id": assert_is_id,
                    "startedAt": assert_is_date,
                }
            ],
        },
    )
