"""extend_tables_for_multi_asset

Revision ID: f85281706898
Revises: 7bfa82ea0b67
Create Date: 2025-10-23 08:40:36.442717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f85281706898'
down_revision: Union[str, Sequence[str], None] = '7bfa82ea0b67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add direction and margin_used columns for multi-asset support."""
    # Extend current_holdings table
    with op.batch_alter_table('current_holdings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('direction', sa.String(10), nullable=False, server_default='long'))
        batch_op.add_column(sa.Column('margin_used', sa.Float(), nullable=False, server_default='0.0'))

    # Extend investment_records table
    with op.batch_alter_table('investment_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('direction', sa.String(10), nullable=False, server_default='long'))
        batch_op.add_column(sa.Column('margin_used', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    """Downgrade schema: Remove direction and margin_used columns."""
    # Remove columns from investment_records
    with op.batch_alter_table('investment_records', schema=None) as batch_op:
        batch_op.drop_column('margin_used')
        batch_op.drop_column('direction')

    # Remove columns from current_holdings
    with op.batch_alter_table('current_holdings', schema=None) as batch_op:
        batch_op.drop_column('margin_used')
        batch_op.drop_column('direction')
