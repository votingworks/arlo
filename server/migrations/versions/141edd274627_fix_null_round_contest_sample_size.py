# pylint: disable=invalid-name
"""Fix null round_contest.sample_size

Revision ID: 141edd274627
Revises: 9d9c4e058cb2
Create Date: 2021-05-04 18:27:47.826265+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "141edd274627"
down_revision = "9d9c4e058cb2"
branch_labels = None
depends_on = None


def upgrade():
    # In a previous migration (07859b6b370b - JSON sample sizes), we converted
    # RoundContest.sample_size from int to JSON, but didn't handle the null case
    # correctly. null should have stayed null, but instead we converted it to a
    # JSON object with field `size` null, which is invalid.
    #
    # Here, we correct that by setting RoundContest.sample_size back to null.
    op.execute(
        """
        UPDATE round_contest
        SET sample_size = null
        WHERE sample_size ->> 'size' is null
        """
    )


def downgrade():  # pragma: no cover
    pass
