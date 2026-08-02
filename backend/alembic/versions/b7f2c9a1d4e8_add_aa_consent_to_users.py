"""add account-aggregation consent to users (task 2.1)

Revision ID: b7f2c9a1d4e8
Revises: 67a356db7043
Create Date: 2026-08-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7f2c9a1d4e8'
down_revision: Union[str, Sequence[str], None] = '67a356db7043'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "aa_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("aa_consent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "aa_consent_at")
    op.drop_column("users", "aa_consent")
