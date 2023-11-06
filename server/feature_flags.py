from .models import Election


def is_enabled_sample_extra_batches_by_counting_group(election: Election):
    return election.organization_id in [
        "b216ad0d-1481-44e4-a2c1-95da40175084",  # Georgia
        "test_org_sample_extra_batches_by_counting_group",  # For tests
    ]
