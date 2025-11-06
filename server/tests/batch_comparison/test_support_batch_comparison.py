from flask.testing import FlaskClient

from ..helpers import *


def test_support_get_jurisdiction_batch_comparison(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    compare_json(
        json.loads(rv.data),
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "organization": {
                "id": org_id,
                "name": "Test Org test_support_get_jurisdiction_batch_comparison",
            },
            "election": {
                "id": election_id,
                "auditName": "Test Audit test_support_get_jurisdiction_batch_comparison",
                "auditType": "BATCH_COMPARISON",
                "online": False,
                "deletedAt": None,
            },
            "jurisdictionAdmins": [{"email": default_ja_email(election_id)}],
            "auditBoards": [],
            "recordedResultsAt": None,
        },
    )


def test_support_combined_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    sampled_batches = json.loads(rv.data)["batches"]
    all_batches = Batch.query.filter_by(jurisdiction_id=jurisdiction_ids[0]).all()
    unsampled_batches = [
        batch
        for batch in all_batches
        if batch.id not in [sampled_batch["id"] for sampled_batch in sampled_batches]
    ]

    # Must be authenticated as an audit admin to use this helper
    def count_num_batches_audited():
        rv = client.get(f"/api/election/{election_id}/jurisdiction")
        jurisdictions = json.loads(rv.data)["jurisdictions"]
        jurisdiction = next(
            (j for j in jurisdictions if j["id"] == jurisdiction_ids[0]), None
        )
        assert jurisdiction is not None
        return jurisdiction["currentRoundStatus"]["numUniqueAudited"]

    # Initially, no combined batches
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/batches")
    response = json.loads(rv.data)
    assert response["batches"] == [
        dict(
            id=batch.id,
            name=batch.name,
        )
        for batch in all_batches
    ]
    assert response["combinedBatches"] == []

    # Create a combined batch
    combined_batch_1_sub_batch_ids = [
        # Use two sampled batches and one unsampled batch to cover all our bases
        sampled_batches[0]["id"],
        sampled_batches[1]["id"],
        unsampled_batches[0].id,
    ]
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 1",
            subBatchIds=combined_batch_1_sub_batch_ids,
        ),
    )
    assert_ok(rv)

    # Check that the combined batch is there
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/batches")
    response = json.loads(rv.data)
    assert response["combinedBatches"] == [
        dict(
            name="Combined Batch 1",
            subBatches=[
                dict(
                    id=sampled_batches[0]["id"],
                    name=sampled_batches[0]["name"],
                ),
                dict(
                    id=sampled_batches[1]["id"],
                    name=sampled_batches[1]["name"],
                ),
                dict(
                    id=unsampled_batches[0].id,
                    name=unsampled_batches[0].name,
                ),
            ],
        )
    ]

    # Ensure that a computation that has to account for combined batches doesn't crash. This
    # specific API call has crashed in the past.
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    assert json.loads(rv.data) == {}

    # Ensure that no batches are considered audited to begin with
    assert count_num_batches_audited() == 0

    # Record some audit results for the combined batch
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    combined_sampled_batches = json.loads(rv.data)["batches"]
    combined_batch = next(
        batch
        for batch in combined_sampled_batches
        if batch["name"] == "Combined Batch 1"
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{combined_batch['id']}/results",
        [
            {
                "name": "Tally Sheet #1",
                "results": {choice["id"]: 1 for choice in contest["choices"]},
            }
        ],
    )
    assert_ok(rv)

    # Ensure that both sampled batches in the combined batch are considered audited
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert count_num_batches_audited() == 2

    # Create another combined batch
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    combined_batch_2_sub_batch_ids = [
        sampled_batches[2]["id"],
        unsampled_batches[1].id,
    ]
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 2",
            subBatchIds=combined_batch_2_sub_batch_ids,
        ),
    )

    # Delete the first combined batch
    rv = client.delete(
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches/{response['combinedBatches'][0]['name']}"
    )
    assert_ok(rv)

    # Check that the first combined batch is gone
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/batches")
    response = json.loads(rv.data)
    assert response["combinedBatches"] == [
        dict(
            name="Combined Batch 2",
            subBatches=[
                dict(
                    id=sampled_batches[2]["id"],
                    name=sampled_batches[2]["name"],
                ),
                dict(
                    id=unsampled_batches[1].id,
                    name=unsampled_batches[1].name,
                ),
            ],
        )
    ]

    # The sub batches should have their tallies cleared
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    for batch in batches:
        if batch["id"] in combined_batch_1_sub_batch_ids:
            assert batch["resultTallySheets"] == []

    # Ensure that we're back to no batches being considered audited
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert count_num_batches_audited() == 0


def test_support_invalid_combined_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)

    jurisdiction_1_batches = Batch.query.filter_by(
        jurisdiction_id=jurisdiction_ids[0]
    ).all()
    unsampled_j1_batches = [
        batch for batch in jurisdiction_1_batches if len(batch.draws) == 0
    ]
    jurisdiction_2_batches = Batch.query.filter_by(
        jurisdiction_id=jurisdiction_ids[1]
    ).all()

    # Invalid jurisdiction
    rv = post_json(
        client,
        "/api/support/jurisdictions/not-a-real-jurisdiction/combined-batches",
    )
    assert rv.status_code == 404

    # Invalid JSON
    for invalid_json in [
        dict(),
        dict(subBatchIds=[jurisdiction_1_batches[0].id, jurisdiction_1_batches[1].id]),
        dict(name="Combined Batch 1"),
        dict(name="Combined Batch 1", subBatchIds=[]),
        dict(name="Combined Batch 1", subBatchIds=[jurisdiction_1_batches[0].id]),
        dict(
            name="",
            subBatchIds=[jurisdiction_1_batches[0].id, jurisdiction_1_batches[1].id],
        ),
    ]:
        rv = post_json(
            client,
            f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
            invalid_json,
        )
        assert rv.status_code == 400

    # Invalid subBatchIds
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 1",
            subBatchIds=[jurisdiction_1_batches[0].id, jurisdiction_2_batches[0].id],
        ),
    )
    assert rv.status_code == 400

    # No sampled batches
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 1",
            subBatchIds=[batch.id for batch in unsampled_j1_batches],
        ),
    )
    assert rv.status_code == 409

    # Create one valid combined batch
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 1",
            subBatchIds=[jurisdiction_1_batches[0].id, jurisdiction_1_batches[1].id],
        ),
    )
    assert_ok(rv)

    # Can't reuse the same name
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 1",
            subBatchIds=[jurisdiction_1_batches[2].id, jurisdiction_1_batches[3].id],
        ),
    )
    assert rv.status_code == 409

    # Can't reuse any of the subBatchIds
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        dict(
            name="Combined Batch 2",
            subBatchIds=[jurisdiction_1_batches[0].id, jurisdiction_1_batches[2].id],
        ),
    )
    assert rv.status_code == 409

    # Can't delete a non-existent combined batch
    rv = client.delete(
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches/non-existent"
    )
    assert rv.status_code == 404
