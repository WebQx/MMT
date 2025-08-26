"""idempotency key table

Revision ID: 0002_idempotency
Revises: 0001_initial
Create Date: 2025-08-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0002_idempotency'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_index('ix_idempotency_expires_at', 'idempotency_keys', ['expires_at'])


def downgrade():
    op.drop_index('ix_idempotency_expires_at', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')