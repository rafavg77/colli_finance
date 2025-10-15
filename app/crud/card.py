from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Card


class CardCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, card_id: int, user_id: int) -> Card | None:
        result = await db.execute(select(Card).where(Card.id == card_id, Card.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: int) -> list[Card]:
        result = await db.execute(select(Card).where(Card.user_id == user_id))
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, user_id: int, **kwargs) -> Card:
        card = Card(user_id=user_id, **kwargs)
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def update(db: AsyncSession, card: Card, **kwargs) -> Card:
        for field, value in kwargs.items():
            if value is not None:
                setattr(card, field, value)
        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def delete(db: AsyncSession, card: Card) -> None:
        await db.delete(card)
        await db.commit()
