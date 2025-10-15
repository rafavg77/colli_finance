"""
Add attachments table

Revision ID: 0004_add_attachments
Revises: 0003_add_composite_indexes
Create Date: 2025-10-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004_add_attachments'
down_revision: Union[str, None] = '0003_add_composite_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=True),
        sa.Column('transfer_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attachments_id', 'attachments', ['id'], unique=False)
    op.create_index('ix_attachments_user_id', 'attachments', ['user_id'], unique=False)
    op.create_index('ix_attachments_transaction_id', 'attachments', ['transaction_id'], unique=False)
    op.create_index('ix_attachments_transfer_id', 'attachments', ['transfer_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_attachments_transfer_id', table_name='attachments')
    op.drop_index('ix_attachments_transaction_id', table_name='attachments')
    op.drop_index('ix_attachments_user_id', table_name='attachments')
    op.drop_index('ix_attachments_id', table_name='attachments')
    op.drop_table('attachments')
