"""add inner_id

Revision ID: e76c2ca5562e
Revises: 54fee6a7ecd8
Create Date: 2023-02-28 22:29:31.595257

"""

from alembic import op
from alembic import context
import sqlalchemy as sa
from sqlalchemy.sql import text
from labelu.alembic_labelu.alembic_labelu_tools import column_exist_in_table


# revision identifiers, used by Alembic.
revision = "e76c2ca5562e"
down_revision = "54fee6a7ecd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    add inner_id and last_sample_inner_id columns in the task and sample tables
    """
    with context.begin_transaction():
        if not column_exist_in_table("task", "last_sample_inner_id"):
            with op.batch_alter_table("task", recreate="always") as batch_op_task:
                batch_op_task.add_column(
                    sa.Column(
                        "last_sample_inner_id",
                        sa.Integer(),
                        nullable=True,
                        comment="The last inner id of sample in a task",
                        server_default=text("0"),
                    ),
                    insert_before="config",
                )
        if not column_exist_in_table("task_sample", "inner_id"):
            with op.batch_alter_table(
                "task_sample", recreate="always"
            ) as batch_op_task_sample:
                batch_op_task_sample.add_column(
                    sa.Column(
                        "inner_id",
                        sa.Integer(),
                        nullable=True,
                        comment="sample id in a task",
                    ),
                    insert_after="id",
                )

        op.execute(
            text(
                "UPDATE task SET last_sample_inner_id=(SELECT sample_number FROM ( SELECT task_id, COUNT(id) AS sample_number FROM task_sample GROUP BY task_id ) task_sample_number WHERE task.id=task_sample_number.task_id )"
            )
        )
        op.execute(
            text(
                "UPDATE task_sample SET inner_id=(SELECT newid FROM ( SELECT t1.id, COUNT(*) AS newid FROM task_sample t1 JOIN task_sample t2 ON t2.task_id = t1.task_id AND (t2.created_at < t1.created_at OR (t2.created_at = t1.created_at AND t2.id <= t1.id)) GROUP BY t1.id) AS derived WHERE derived.id = task_sample.id)"
            )
        )


def downgrade() -> None:
    """
    delete inner_id and last_sample_inner_id columns in the task and sample tables
    """
    op.drop_column("task_sample", "inner_id")
    op.drop_column("task", "last_sample_inner_id")
