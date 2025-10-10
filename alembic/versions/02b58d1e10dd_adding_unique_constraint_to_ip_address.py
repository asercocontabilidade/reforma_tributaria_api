"""adding unique constraint to ip_address

Revision ID: 02b58d1e10dd
Revises: 187cd04ea76b
Create Date: 2025-10-09 13:58:48.593888+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02b58d1e10dd'
down_revision: Union[str, Sequence[str], None] = '187cd04ea76b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adiciona a restrição UNIQUE à coluna existente.
    op.create_unique_constraint(
        "uq_users_ip_address", # Nome da restrição (ex: "uq_tabela_coluna")
        "users",
        ["ip_address"]
    )

def downgrade() -> None:
    # Remove a restrição
    op.drop_constraint("uq_users_ip_address", "users", type_='unique')
