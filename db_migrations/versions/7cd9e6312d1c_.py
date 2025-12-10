"""empty message

Revision ID: 7cd9e6312d1c
Revises: c83507441c88, 2e9e85e8b1f8
Create Date: 2024-11-25 22:07:29.369466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7cd9e6312d1c'
down_revision: Union[str, None] = ('c83507441c88', '2e9e85e8b1f8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
