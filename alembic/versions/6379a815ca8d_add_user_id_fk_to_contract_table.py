"""add user_id FK to contract table

Revision ID: 6379a815ca8d
Revises: 473659f1888d
Create Date: 2025-11-14 11:40:03.006161+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6379a815ca8d'
down_revision: Union[str, Sequence[str], None] = '473659f1888d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contract",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_contract_user",
        source_table="contract",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_contract_user", "contract", type_="foreignkey")

    op.drop_column("contract", "user_id")
