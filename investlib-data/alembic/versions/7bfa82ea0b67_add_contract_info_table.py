"""add_contract_info_table

Revision ID: 7bfa82ea0b67
Revises: 9fc1324e5000
Create Date: 2025-10-23 08:39:52.065783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bfa82ea0b67'
down_revision: Union[str, Sequence[str], None] = '9fc1324e5000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create contract_info table for futures/options metadata."""
    op.create_table(
        'contract_info',
        sa.Column('contract_code', sa.String(50), primary_key=True),
        sa.Column('contract_type', sa.String(20), nullable=False),  # 'futures' or 'option'
        sa.Column('underlying', sa.String(20), nullable=False),  # Underlying asset symbol
        sa.Column('multiplier', sa.Integer(), nullable=False, server_default='1'),  # Contract multiplier
        sa.Column('margin_rate', sa.Float(), nullable=True),  # For futures
        sa.Column('tick_size', sa.Float(), nullable=True),  # Minimum price movement
        sa.Column('expire_date', sa.Date(), nullable=True),  # Expiration date
        sa.Column('delivery_method', sa.String(20), nullable=True),  # 'physical' or 'cash'
        sa.Column('option_type', sa.String(10), nullable=True),  # 'call' or 'put' for options
        sa.Column('strike_price', sa.Float(), nullable=True),  # Strike price for options
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create index for performance
    op.create_index('ix_contract_type', 'contract_info', ['contract_type'])


def downgrade() -> None:
    """Downgrade schema: Drop contract_info table."""
    op.drop_index('ix_contract_type', table_name='contract_info')
    op.drop_table('contract_info')
