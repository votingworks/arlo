from .models import Election


def is_enabled_sample_extra_batches_by_counting_group(election: Election):
    return election.organization_id in [
        "b216ad0d-1481-44e4-a2c1-95da40175084",  # Georgia
        "a67791e3-90a0-4d4e-a5e7-929f82bf4ce6",  # VotingWorks Internal Sandbox
        "b45800ff-a239-42b3-b285-414cb94d2b6b",  # Ginny's Sandbox
        "b7b99303-b1ac-4b52-8a02-22c10846cff3",  # Audit Specialist Sandbox
        "e348fcfd-bd23-4b96-a003-6c3a79abd240",  # Verified Voting Sandbox
    ]
