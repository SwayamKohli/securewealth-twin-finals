"""add chain index to audit logs

Revision ID: 67a356db7043
Revises: 093283f39350
Create Date: 2026-08-01 22:24:35.377816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67a356db7043'
down_revision: Union[str, Sequence[str], None] = '093283f39350'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "audit_logs",
        sa.Column(
            "chain_index",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_audit_logs_chain_index",
        "audit_logs",
        ["chain_index"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_audit_logs_chain_index",
        table_name="audit_logs",
    )

    op.drop_column(
        "audit_logs",
        "chain_index",
    )