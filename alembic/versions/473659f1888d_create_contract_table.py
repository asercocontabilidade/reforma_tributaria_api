"""create_contract_table

Revision ID: 473659f1888d
Revises: 051faf191d0e
Create Date: 2025-11-13 20:20:48.891977+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '473659f1888d'
down_revision: Union[str, Sequence[str], None] = '051faf191d0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'contract',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type_of_contract', sa.String(length=255), nullable=True),
        sa.Column("date_time_accepted", sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_signature_accepted', sa.Boolean(), nullable=False),
        sa.Column('term_content', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=255), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('contract')
