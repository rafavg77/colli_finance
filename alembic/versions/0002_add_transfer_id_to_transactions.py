"""add transfer_id to transactions

Revision ID: 0002_add_transfer_id
Revises: 0001_initial
Create Date: 2025-10-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_transfer_id"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("transfer_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_transactions_transfer_id"), "transactions", ["transfer_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_transfer_id"), table_name="transactions")
    op.drop_column("transactions", "transfer_id")
