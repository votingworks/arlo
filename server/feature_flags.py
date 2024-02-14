from .models import Election


def is_enabled_sample_extra_batches_by_counting_group(election: Election):
    return election.organization_id in [
        "test_org_sample_extra_batches_by_counting_group",  # For tests
    ]
