"""add_watchlist_table

Revision ID: 9fc1324e5000
Revises: 
Create Date: 2025-10-23 08:39:23.380398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fc1324e5000'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create watchlist table."""
    op.create_table(
        'watchlist',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('group_name', sa.String(50), nullable=False, server_default='default'),
        sa.Column('contract_type', sa.String(20), nullable=False, server_default='stock'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for performance
    op.create_index('ix_watchlist_symbol', 'watchlist', ['symbol'])
    op.create_index('ix_watchlist_group', 'watchlist', ['group_name'])
    op.create_index('ix_watchlist_status', 'watchlist', ['status'])


def downgrade() -> None:
    """Downgrade schema: Drop watchlist table."""
    op.drop_index('ix_watchlist_status', table_name='watchlist')
    op.drop_index('ix_watchlist_group', table_name='watchlist')
    op.drop_index('ix_watchlist_symbol', table_name='watchlist')
    op.drop_table('watchlist')
