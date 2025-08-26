"""async tasks table

Revision ID: 0003_async_tasks
Revises: 0002_idempotency
Create Date: 2025-08-23
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0003_async_tasks'
down_revision = '0002_idempotency'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'async_tasks',
        sa.Column('task_id', sa.String(32), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),  # processing|done|error
        sa.Column('result_text', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_index('ix_async_tasks_created_at', 'async_tasks', ['created_at'])
    op.create_index('ix_async_tasks_updated_at', 'async_tasks', ['updated_at'])


def downgrade():
    op.drop_index('ix_async_tasks_created_at', table_name='async_tasks')
    op.drop_index('ix_async_tasks_updated_at', table_name='async_tasks')
    op.drop_table('async_tasks')
