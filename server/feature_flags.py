from .models import Election


def is_enabled_sample_extra_batches_by_counting_group(election: Election):
    return (
        election.organization_id
        in [
            "b216ad0d-1481-44e4-a2c1-95da40175084",  # Georgia
            "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round",  # For tests
            "TEST-ORG/sample-extra-batches-by-counting-group",  # For tests
        ]
    )


def is_enabled_sample_extra_batches_to_ensure_one_per_jurisdiction(election: Election):
    return election.organization_id in [
        "d563f551-0d7a-4a89-aa45-2f60147d0337",  # Maryland
        "TEST-ORG/sample-extra-batches-to-ensure-one-per-jurisdiction",  # For tests
    ]


def is_enabled_automatically_end_audit_after_one_round(election: Election):
    return (
        election.organization_id
        in [
            "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round",  # For tests
        ]
    )
