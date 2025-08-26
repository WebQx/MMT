"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'transcripts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('enrichment', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(32), nullable=False),
        sa.Column('fhir_document_id', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_table(
        'smart_sessions',
        sa.Column('session_id', sa.String(48), primary_key=True),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('smart_sessions')
    op.drop_table('transcripts')