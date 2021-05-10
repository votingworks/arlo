# pylint: disable=invalid-name
"""On delete cleanup

Revision ID: d0fc64ab8b98
Revises: 141edd274627
Create Date: 2021-05-10 18:49:43.227048+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d0fc64ab8b98"
down_revision = "141edd274627"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "audit_board", "round_id", existing_type=sa.VARCHAR(length=200), nullable=False
    )
    op.drop_constraint("round_draw_sample_task_id_fkey", "round", type_="foreignkey")
    op.create_foreign_key(
        op.f("round_draw_sample_task_id_fkey"),
        "round",
        "background_task",
        ["draw_sample_task_id"],
        ["id"],
        ondelete="set null",
    )


def downgrade():  # pragma: no cover
    pass
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_constraint(
    #     op.f("round_draw_sample_task_id_fkey"), "round", type_="foreignkey"
    # )
    # op.create_foreign_key(
    #     "round_draw_sample_task_id_fkey",
    #     "round",
    #     "background_task",
    #     ["draw_sample_task_id"],
    #     ["id"],
    #     ondelete="CASCADE",
    # )
    # op.alter_column(
    #     "audit_board", "round_id", existing_type=sa.VARCHAR(length=200), nullable=True
    # )
    # ### end Alembic commands ###
