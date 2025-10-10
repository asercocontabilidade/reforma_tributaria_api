"""adding ip column in users table

Revision ID: 187cd04ea76b
Revises: d3a8af7dd9d3
Create Date: 2025-10-09 12:18:25.378810+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '187cd04ea76b'
down_revision: Union[str, Sequence[str], None] = 'd3a8af7dd9d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('ip_address', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'ip_address')
