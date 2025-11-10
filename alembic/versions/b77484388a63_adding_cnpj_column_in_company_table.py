"""adding cnpj column in company table

Revision ID: b77484388a63
Revises: b5b35a0ad694
Create Date: 2025-11-07 13:44:58.163424+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b77484388a63'
down_revision: Union[str, Sequence[str], None] = 'b5b35a0ad694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('company', sa.Column('cnpj', sa.String(length=255), nullable=False))

def downgrade() -> None:
    op.drop_column('company', 'cnpj')
