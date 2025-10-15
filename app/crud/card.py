from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Card
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CardCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, card_id: int, user_id: int) -> Card | None:
        result = await db.execute(select(Card).where(Card.id == card_id, Card.user_id == user_id))
        card = result.scalar_one_or_none()
        logger.debug(
            "Fetched card by id",
            extra={
                "details": {
                    "event": "card_lookup_id",
                    "extra": {"card_id": card_id, "user_id": user_id, "found": bool(card)},
                }
            },
        )
        return card

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: int) -> list[Card]:
        result = await db.execute(select(Card).where(Card.user_id == user_id))
        cards = list(result.scalars().all())
        logger.debug(
            "Listed cards for user",
            extra={"details": {"event": "card_list", "extra": {"user_id": user_id, "count": len(cards)}}},
        )
        return cards

    @staticmethod
    async def create(db: AsyncSession, user_id: int, **kwargs) -> Card:
        card = Card(user_id=user_id, **kwargs)
        db.add(card)
        await db.commit()
        await db.refresh(card)
        logger.info(
            "Card created",
            extra={
                "details": {
                    "event": "card_create",
                    "extra": {"card_id": card.id, "user_id": user_id},
                }
            },
        )
        return card

    @staticmethod
    async def update(db: AsyncSession, card: Card, **kwargs) -> Card:
        for field, value in kwargs.items():
            if value is not None:
                setattr(card, field, value)
        await db.commit()
        await db.refresh(card)
        logger.info(
            "Card updated",
            extra={
                "details": {
                    "event": "card_update",
                    "extra": {"card_id": card.id, "updated_fields": [field for field, value in kwargs.items() if value is not None]},
                }
            },
        )
        return card

    @staticmethod
    async def delete(db: AsyncSession, card: Card) -> None:
        await db.delete(card)
        await db.commit()
        logger.warning(
            "Card deleted",
            extra={"details": {"event": "card_delete", "extra": {"card_id": card.id, "user_id": card.user_id}}},
        )
