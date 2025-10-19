"""add banks table, operation date column, and listener scaffolding

Revision ID: 0005_banks_listener
Revises: 0004_add_attachments
Create Date: 2025-10-19
"""

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_banks_listener"
down_revision = "0004_add_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Banks catalog
    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_banks_slug", "banks", ["slug"], unique=True)

    # Default banks
    raw_banks = os.getenv("BANKS_LIST", "")
    banks: list[tuple[str, str, str]] = []
    for entry in raw_banks.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = [part.strip() for part in entry.split(":")]
        if len(parts) != 3:
            raise ValueError(
                "BANKS_LIST debe definir cada banco como 'name:slug:display_name' separado por ';'"
            )
        banks.append((parts[0], parts[1], parts[2]))

    for name, slug, display_name in banks:
        op.execute(
            sa.text(
                """
                INSERT INTO banks (name, slug, display_name, is_active)
                VALUES (:name, :slug, :display_name, TRUE)
                ON CONFLICT (slug) DO NOTHING
                """
            ),
            {"name": name, "slug": slug, "display_name": display_name},
        )

    # Card enhancements
    op.add_column("cards", sa.Column("bank_id", sa.Integer(), nullable=True))
    op.add_column("cards", sa.Column("billing_cycle_day", sa.SmallInteger(), nullable=True))
    op.add_column("cards", sa.Column("payment_due_day", sa.SmallInteger(), nullable=True))
    op.add_column("cards", sa.Column("grace_days", sa.SmallInteger(), nullable=True))

    op.create_foreign_key(
        "fk_cards_bank_id", "cards", "banks", ["bank_id"], ["id"], ondelete="RESTRICT"
    )

    # Ensure all legacy banks exist in catalog
    op.execute(
        """
     INSERT INTO banks (name, slug, display_name, is_active)
     SELECT DISTINCT c.bank_name,
         regexp_replace(lower(c.bank_name), '[^a-z0-9]+', '_', 'g') AS slug,
         c.bank_name,
         TRUE
     FROM cards c
     LEFT JOIN banks b ON lower(b.display_name) = lower(c.bank_name)
     WHERE c.bank_name IS NOT NULL AND b.id IS NULL
     ON CONFLICT (slug) DO NOTHING
        """
    )

    # Backfill card bank_id using bank display name
    op.execute(
        """
        UPDATE cards AS c
        SET bank_id = b.id
        FROM banks AS b
        WHERE c.bank_name IS NOT NULL
          AND lower(b.display_name) = lower(c.bank_name)
        """
    )

    # Set bank_name from catalog to keep values consistent
    op.execute(
        """
        UPDATE cards AS c
        SET bank_name = b.display_name
        FROM banks AS b
        WHERE c.bank_id = b.id
        """
    )

    # Guard against orphaned records by assigning unknown bank if needed
    op.execute(
        """
        INSERT INTO banks (name, slug, display_name, is_active)
        SELECT 'Unknown', 'unknown', 'Sin banco', TRUE
        WHERE NOT EXISTS (SELECT 1 FROM banks WHERE slug = 'unknown')
        """
    )
    op.execute(
        """
        UPDATE cards
        SET bank_id = (SELECT id FROM banks WHERE slug = 'unknown')
        WHERE bank_id IS NULL
        """
    )

    op.alter_column("cards", "bank_id", existing_type=sa.Integer(), nullable=False)

    # Trigger to keep legacy bank_name in sync
    op.execute(
        """
        CREATE OR REPLACE FUNCTION sync_card_bank_name()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.bank_id IS NOT NULL THEN
                SELECT display_name INTO NEW.bank_name FROM banks WHERE id = NEW.bank_id;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_cards_sync_bank_name
        BEFORE INSERT OR UPDATE ON cards
        FOR EACH ROW
        EXECUTE FUNCTION sync_card_bank_name();
        """
    )

    # Operation date column in transactions
    op.add_column("transactions", sa.Column("operation_date", sa.Date(), nullable=True))
    op.execute("UPDATE transactions SET operation_date = created_at::date")
    op.alter_column("transactions", "operation_date", existing_type=sa.Date(), nullable=False)

    # Refresh supporting indexes to use operation_date instead of created_at
    op.drop_index("ix_transactions_user_transfer_created", table_name="transactions")
    op.drop_index("ix_transactions_user_card_created", table_name="transactions")

    op.create_index(
        "ix_transactions_user_transfer_operation",
        "transactions",
        ["user_id", "transfer_id", "operation_date"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_user_card_operation",
        "transactions",
        ["user_id", "card_id", "operation_date"],
        unique=False,
    )

    # Listener scaffolding
    op.create_table(
        "listener_cred",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'disabled'")),
        sa.Column("google_credentials", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("google_access_token", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_listener_cred_user"),
    )

    op.create_table(
        "listener_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bank_id", sa.Integer(), sa.ForeignKey("banks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_code", sa.String(length=100), nullable=False),
        sa.Column("email_sender", sa.String(length=255), nullable=False),
        sa.Column("subject_pattern", sa.Text(), nullable=True),
        sa.Column("amount_pattern", sa.Text(), nullable=True),
        sa.Column("description_pattern", sa.Text(), nullable=True),
        sa.Column("date_pattern", sa.Text(), nullable=True),
        sa.Column("time_pattern", sa.Text(), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
    sa.Column("template_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("bank_id", "template_code", name="uq_listener_templates_bank_code"),
    )

    op.create_table(
        "listener_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "listener_cred_id",
            sa.Integer(),
            sa.ForeignKey("listener_cred.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "listener_template_id",
            sa.Integer(),
            sa.ForeignKey("listener_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "listener_cred_id", "listener_template_id", "card_id", name="uq_listener_config_binding"
        ),
    )

    op.create_index("ix_listener_templates_bank", "listener_templates", ["bank_id"], unique=False)
    op.create_index("ix_listener_config_card", "listener_config", ["card_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listener_config_card", table_name="listener_config")
    op.drop_table("listener_config")
    op.drop_index("ix_listener_templates_bank", table_name="listener_templates")
    op.drop_table("listener_templates")
    op.drop_table("listener_cred")

    op.drop_index("ix_transactions_user_card_operation", table_name="transactions")
    op.drop_index("ix_transactions_user_transfer_operation", table_name="transactions")

    op.create_index(
        "ix_transactions_user_card_created",
        "transactions",
        ["user_id", "card_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_user_transfer_created",
        "transactions",
        ["user_id", "transfer_id", "created_at"],
        unique=False,
    )

    op.alter_column("transactions", "operation_date", existing_type=sa.Date(), nullable=True)
    op.drop_column("transactions", "operation_date")

    op.execute("DROP TRIGGER IF EXISTS trg_cards_sync_bank_name ON cards")
    op.execute("DROP FUNCTION IF EXISTS sync_card_bank_name")

    op.drop_constraint("fk_cards_bank_id", "cards", type_="foreignkey")
    op.drop_column("cards", "grace_days")
    op.drop_column("cards", "payment_due_day")
    op.drop_column("cards", "billing_cycle_day")
    op.drop_column("cards", "bank_id")

    op.drop_index("ix_banks_slug", table_name="banks")
    op.drop_table("banks")
