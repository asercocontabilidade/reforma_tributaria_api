"""creating table customer

Revision ID: 0ea60c18d0b7
Revises: 63f4ecb2683a
Create Date: 2025-10-14 16:43:22.091357+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ea60c18d0b7'
down_revision: Union[str, Sequence[str], None] = '63f4ecb2683a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'customer',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('pro', 'basic', name='roletype'), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('contract_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contract_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cnae_company', sa.String(length=255), nullable=True),
        sa.Column('tax_regime', sa.String(length=255), nullable=True),
        sa.Column('erp_code', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True)
    )

def downgrade() -> None:
    op.drop_table('customer')
