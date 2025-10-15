from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Card, Transaction
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TransactionCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, transaction_id: int, user_id: int) -> Transaction | None:
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        transaction = result.scalar_one_or_none()
        logger.debug(
            "Fetched transaction by id",
            extra={
                "details": {
                    "event": "transaction_lookup_id",
                    "extra": {"transaction_id": transaction_id, "user_id": user_id, "found": bool(transaction)},
                }
            },
        )
        return transaction

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: int) -> list[Transaction]:
        result = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
        transactions = list(result.scalars().all())
        logger.debug(
            "Listed transactions for user",
            extra={
                "details": {"event": "transaction_list", "extra": {"user_id": user_id, "count": len(transactions)}}
            },
        )
        return transactions

    @staticmethod
    async def create(db: AsyncSession, user_id: int, **kwargs) -> Transaction:
        transaction = Transaction(user_id=user_id, **kwargs)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        logger.info(
            "Transaction created",
            extra={
                "details": {
                    "event": "transaction_create",
                    "extra": {"transaction_id": transaction.id, "user_id": user_id, "type": kwargs.get("type")},
                }
            },
        )
        return transaction

    @staticmethod
    async def update(db: AsyncSession, transaction: Transaction, **kwargs) -> Transaction:
        for field, value in kwargs.items():
            if value is not None:
                setattr(transaction, field, value)
        await db.commit()
        await db.refresh(transaction)
        logger.info(
            "Transaction updated",
            extra={
                "details": {
                    "event": "transaction_update",
                    "extra": {
                        "transaction_id": transaction.id,
                        "updated_fields": [field for field, value in kwargs.items() if value is not None],
                    },
                }
            },
        )
        return transaction

    @staticmethod
    async def delete(db: AsyncSession, transaction: Transaction) -> None:
        await db.delete(transaction)
        await db.commit()
        logger.warning(
            "Transaction deleted",
            extra={
                "details": {
                    "event": "transaction_delete",
                    "extra": {"transaction_id": transaction.id, "user_id": transaction.user_id},
                }
            },
        )

    @staticmethod
    async def transfer(
        db: AsyncSession,
        *,
        user_id: int,
        source_card_id: int,
        destination_card_id: int,
        amount: Decimal,
        description: str | None = None,
        category_id: int | None = None,
    ) -> tuple[Transaction, Transaction]:
        """Create a pair of transactions to represent a transfer between user's own cards.

        - Source card: expenses = amount
        - Destination card: income = amount
        Both transactions share description/category and are marked executed=True.
        """
        if source_card_id == destination_card_id:
            raise ValueError("La tarjeta origen y destino no pueden ser la misma")

        # Prepare payloads
        desc = description or "Transferencia entre cuentas"
        expense_kwargs = dict(
            user_id=user_id,
            card_id=source_card_id,
            description=desc,
            category_id=category_id,
            income=Decimal("0.00"),
            expenses=amount,
            executed=True,
        )
        income_kwargs = dict(
            user_id=user_id,
            card_id=destination_card_id,
            description=desc,
            category_id=category_id,
            income=amount,
            expenses=Decimal("0.00"),
            executed=True,
        )

        # Execute atomically; persist then set a shared transfer_id (use expense_tx id)
        expense_tx = Transaction(**expense_kwargs)
        income_tx = Transaction(**income_kwargs)
        db.add_all([expense_tx, income_tx])
        await db.flush()  # get IDs without commit
        transfer_id = expense_tx.id  # use first id as linkage
        expense_tx.transfer_id = transfer_id
        income_tx.transfer_id = transfer_id
        await db.commit()
        await db.refresh(expense_tx)
        await db.refresh(income_tx)

        logger.info(
            "Transfer completed",
            extra={
                "details": {
                    "event": "transfer",
                    "extra": {
                        "user_id": user_id,
                        "source_card_id": source_card_id,
                        "destination_card_id": destination_card_id,
                        "amount": str(amount),
                        "expense_tx": expense_tx.id,
                        "income_tx": income_tx.id,
                    },
                }
            },
        )
        return expense_tx, income_tx

    async def summarize_by_card(
        db: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        stmt = (
            select(
                Transaction.card_id,
                Card.card_name,
                Card.bank_name,
                func.coalesce(func.sum(Transaction.income), 0).label("income_total"),
                func.coalesce(func.sum(Transaction.expenses), 0).label("expenses_total"),
            )
            .join(Card, Card.id == Transaction.card_id)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date,
                    Transaction.created_at < end_date,
                )
            )
            .group_by(Transaction.card_id, Card.card_name, Card.bank_name)
        )
        result = await db.execute(stmt)
        rows = [dict(row._mapping) for row in result.all()]
        logger.debug(
            "Transaction summary generated",
            extra={
                "details": {
                    "event": "transaction_summary",
                    "extra": {
                        "user_id": user_id,
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "count": len(rows),
                    },
                }
            },
        )
        return rows
