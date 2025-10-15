"""add composite indexes for transfer and balance queries

Revision ID: 0003_add_composite_indexes
Revises: 0002_add_transfer_id
Create Date: 2025-10-15

Motivation:
- (user_id, transfer_id): acelera GET /transfers/{transfer_id}
- (user_id, transfer_id, created_at): acelera listado paginado por transfer ordenado por fecha más reciente
- (user_id, card_id): acelera cómputo de balance por tarjeta (SUM income - expenses)
- (user_id, card_id, created_at): útil si consultas/resumes por rangos de fecha
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_composite_indexes"
down_revision = "0002_add_transfer_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Índices para transferencias
    op.create_index(
        "ix_transactions_user_transfer",
        "transactions",
        ["user_id", "transfer_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_user_transfer_created",
        "transactions",
        ["user_id", "transfer_id", "created_at"],
        unique=False,
    )

    # Índices para balance/consultas por tarjeta
    op.create_index(
        "ix_transactions_user_card",
        "transactions",
        ["user_id", "card_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_user_card_created",
        "transactions",
        ["user_id", "card_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_user_card_created", table_name="transactions")
    op.drop_index("ix_transactions_user_card", table_name="transactions")
    op.drop_index("ix_transactions_user_transfer_created", table_name="transactions")
    op.drop_index("ix_transactions_user_transfer", table_name="transactions")
