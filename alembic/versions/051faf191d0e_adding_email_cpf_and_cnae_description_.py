"""adding email, cpf and cnae_description in company table

Revision ID: 051faf191d0e
Revises: b77484388a63
Create Date: 2025-11-12 13:20:40.402254+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '051faf191d0e'
down_revision: Union[str, Sequence[str], None] = 'b77484388a63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('company', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('company', sa.Column('cpf', sa.String(length=50), nullable=True))
    op.add_column('company', sa.Column('cnae_description', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('company', 'email')
    op.drop_column('company', 'cpf')
    op.drop_column('company', 'cnae_description')
