from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.core.security import get_password_hash


class UserCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, *, name: str, phone: str, telegram_id: str | None, email: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        user = User(name=name, phone=phone, telegram_id=telegram_id, email=email, password=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User, **kwargs) -> User:
        if "password" in kwargs and kwargs["password"]:
            kwargs["password"] = get_password_hash(kwargs["password"])
        for field, value in kwargs.items():
            if value is not None:
                setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()
