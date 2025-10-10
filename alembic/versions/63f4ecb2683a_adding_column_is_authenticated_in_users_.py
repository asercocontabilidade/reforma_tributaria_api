"""adding column is_authenticated in users table

Revision ID: 63f4ecb2683a
Revises: 02b58d1e10dd
Create Date: 2025-10-09 18:29:33.809681+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63f4ecb2683a'
down_revision: Union[str, Sequence[str], None] = '02b58d1e10dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_authenticated', sa.Boolean(), nullable=False))

def downgrade() -> None:
    op.drop_column('users', 'is_authenticated')