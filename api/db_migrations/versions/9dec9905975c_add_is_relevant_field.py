"""add is_relevant field

Revision ID: 9dec9905975c
Revises: d0a4fad28f8f
Create Date: 2025-04-26 16:13:06.160757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9dec9905975c'
down_revision: Union[str, None] = 'd0a4fad28f8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sourced_documents', sa.Column('is_relevant', sa.Boolean(), nullable=False, server_default="FALSE"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sourced_documents', 'is_relevant')
    # ### end Alembic commands ###
