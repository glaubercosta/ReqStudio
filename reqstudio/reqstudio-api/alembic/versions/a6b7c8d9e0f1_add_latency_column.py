"""add latency column

Revision ID: a6b7c8d9e0f1
Revises: a55b3c3e98f0
Create Date: 2026-04-03 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'a55b3c3e98f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated manually ###
    op.add_column('messages', sa.Column('latency_ms', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated manually ###
    op.drop_column('messages', 'latency_ms')
    # ### end Alembic commands ###
