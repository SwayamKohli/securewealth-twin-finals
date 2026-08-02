"""add bank-grade customer_id (SecureWealth ID) to users — phone login removed

Revision ID: c4d8e2f7a9b1
Revises: b7f2c9a1d4e8
Create Date: 2026-08-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d8e2f7a9b1'
down_revision: Union[str, Sequence[str], None] = 'b7f2c9a1d4e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("customer_id", sa.String(20), nullable=True),
    )
    # Backfill existing users with a deterministic SecureWealth ID
    op.execute(
        "UPDATE users SET customer_id = 'SW' || UPPER(SUBSTR(MD5(user_id::text), 1, 8)) "
        "WHERE customer_id IS NULL"
    )
    op.create_unique_constraint("uq_users_customer_id", "users", ["customer_id"])
    op.create_index("ix_users_customer_id", "users", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_users_customer_id", table_name="users")
    op.drop_constraint("uq_users_customer_id", "users", type_="unique")
    op.drop_column("users", "customer_id")
