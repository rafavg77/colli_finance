from datetime import datetime
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
                    Transaction.created_at <= end_date,
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
