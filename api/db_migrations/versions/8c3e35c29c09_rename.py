"""rename

Revision ID: 8c3e35c29c09
Revises: 6dc380cca19a
Create Date: 2024-11-25 23:33:25.624975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8c3e35c29c09'
down_revision: Union[str, None] = '6dc380cca19a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('thread_message_feedback', sa.Column('feedback_id', sa.Uuid(), nullable=False))
    op.drop_column('thread_message_feedback', 'feeddback_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('thread_message_feedback', sa.Column('feeddback_id', sa.UUID(), autoincrement=False, nullable=False))
    op.drop_column('thread_message_feedback', 'feedback_id')
    # ### end Alembic commands ###