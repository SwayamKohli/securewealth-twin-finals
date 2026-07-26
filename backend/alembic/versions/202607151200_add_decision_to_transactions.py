"""
Add decision field to transactions table

Revision ID: 202607151200
Revises: a18012f2eb48
Create Date: 2026-07-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '202607151200'
down_revision: Union[str, Sequence[str], None] = 'a18012f2eb48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add decision column to transactions table
    op.add_column('transactions', 
                  sa.Column('decision', sa.String(length=20), nullable=True))
    
    # Add decision_timestamp column to track when decision was made
    op.add_column('transactions', 
                  sa.Column('decision_timestamp', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transactions', 'decision_timestamp')
    op.drop_column('transactions', 'decision')