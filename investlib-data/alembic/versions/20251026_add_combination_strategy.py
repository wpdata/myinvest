"""Migration 004: Add combination_strategy table for multi-leg strategies

Revision ID: 20251026_add_combination
Revises: 20251024_extend_tables_multi_asset
Create Date: 2025-10-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '20251026_add_combination'
down_revision = '20251024_extend_tables_multi_asset'
branch_labels = None
depends_on = None


def upgrade():
    """Create combination_strategy table."""
    # SQLite batch mode for schema changes
    with op.batch_alter_table('combination_strategy', schema=None) as batch_op:
        pass  # Placeholder - table doesn't exist yet

    # Create table
    op.create_table(
        'combination_strategy',
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('strategy_name', sa.String(100), nullable=False),
        sa.Column('strategy_type', sa.String(50), nullable=False),
        sa.Column('legs', sa.Text(), nullable=False),  # JSON string
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('strategy_id')
    )

    # Create indexes
    op.create_index('ix_combination_strategy_type', 'combination_strategy', ['strategy_type'])
    op.create_index('ix_combination_status', 'combination_strategy', ['status'])


def downgrade():
    """Drop combination_strategy table."""
    op.drop_index('ix_combination_status', table_name='combination_strategy')
    op.drop_index('ix_combination_strategy_type', table_name='combination_strategy')
    op.drop_table('combination_strategy')
