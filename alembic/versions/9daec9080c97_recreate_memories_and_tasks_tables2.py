"""recreate memories and tasks tables2

Revision ID: 9daec9080c97
Revises: ab45f30f6855
Create Date: 2025-09-17 00:15:02.663604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '9daec9080c97'
down_revision: Union[str, Sequence[str], None] = 'ab45f30f6855'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Drop old tables if they exist
    op.drop_table('memories', if_exists=True)
    op.drop_table('tasks', if_exists=True)
    op.drop_table('conversation_history', if_exists=True)

    # Recreate tables
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('memory_type', sa.String(50), server_default="general"),
        sa.Column('meta_data', sa.JSON, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('embedding', Vector(1536))
    )

    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('due_time', sa.TIMESTAMP(timezone=True)),
        sa.Column('status', sa.String, server_default="pending"),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('response', sa.Text, nullable=False),
        sa.Column('emotion', sa.String(20)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('conversation_history')
    op.drop_table('tasks')
    op.drop_table('memories')