"""add customer_id FK to users table

Revision ID: b5b35a0ad694
Revises: 0ea60c18d0b7
Create Date: 2025-10-22 18:58:49.648843+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5b35a0ad694'
down_revision: Union[str, Sequence[str], None] = '0ea60c18d0b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("company_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_user_company",
        source_table="users",
        referent_table="company",
        local_cols=["company_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_company", "users", type_="foreignkey")   # <- troque table_name se necessário
    op.drop_column("users", "company_id")