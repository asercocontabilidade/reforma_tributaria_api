"""create code table

Revision ID: a876fcfb9a42
Revises: 6379a815ca8d
Create Date: 2025-12-17 16:50:37.195213+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a876fcfb9a42'
down_revision: Union[str, Sequence[str], None] = '6379a815ca8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "code",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column(
            "is_code_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
            unique=True
        ),
    )


def downgrade():
    op.drop_table("code")
