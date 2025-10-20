from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bank
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BankCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, bank_id: int) -> Bank | None:
        result = await db.execute(select(Bank).where(Bank.id == bank_id))
        bank = result.scalar_one_or_none()
        logger.debug(
            "Fetched bank by id",
            extra={
                "details": {
                    "event": "bank_lookup_id",
                    "extra": {"bank_id": bank_id, "found": bool(bank)},
                }
            },
        )
        return bank

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Bank | None:
        result = await db.execute(select(Bank).where(Bank.slug == slug))
        bank = result.scalar_one_or_none()
        logger.debug(
            "Fetched bank by slug",
            extra={
                "details": {
                    "event": "bank_lookup_slug",
                    "extra": {"slug": slug, "found": bool(bank)},
                }
            },
        )
        return bank

    @staticmethod
    async def list_active(db: AsyncSession) -> list[Bank]:
        result = await db.execute(select(Bank).where(Bank.is_active.is_(True)).order_by(Bank.display_name))
        banks = list(result.scalars().all())
        logger.debug(
            "Listed active banks",
            extra={"details": {"event": "bank_list", "extra": {"count": len(banks)}}},
        )
        return banks

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Bank:
        bank = Bank(**kwargs)
        db.add(bank)
        await db.commit()
        await db.refresh(bank)
        logger.info(
            "Bank created",
            extra={"details": {"event": "bank_create", "extra": {"bank_id": bank.id, "slug": bank.slug}}},
        )
        return bank

    @staticmethod
    async def update(db: AsyncSession, bank: Bank, **kwargs) -> Bank:
        for field, value in kwargs.items():
            if value is not None:
                setattr(bank, field, value)
        await db.commit()
        await db.refresh(bank)
        logger.info(
            "Bank updated",
            extra={"details": {"event": "bank_update", "extra": {"bank_id": bank.id}}},
        )
        return bank

    @staticmethod
    async def delete(db: AsyncSession, bank: Bank) -> None:
        await db.delete(bank)
        await db.commit()
        logger.warning(
            "Bank deleted",
            extra={"details": {"event": "bank_delete", "extra": {"bank_id": bank.id}}},
        )
