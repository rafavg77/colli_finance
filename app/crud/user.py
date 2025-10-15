from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.core.security import get_password_hash
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UserCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        logger.debug(
            "Fetched user by id",
            extra={"details": {"event": "user_lookup_id", "extra": {"user_id": user_id, "found": bool(user)}}},
        )
        return user

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        logger.debug(
            "Fetched user by phone",
            extra={
                "details": {
                    "event": "user_lookup_phone",
                    "extra": {"phone_suffix": phone[-4:], "found": bool(user)},
                }
            },
        )
        return user

    @staticmethod
    async def create(db: AsyncSession, *, name: str, phone: str, telegram_id: str | None, email: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        user = User(name=name, phone=phone, telegram_id=telegram_id, email=email, password=hashed_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(
            "User created",
            extra={
                "details": {
                    "event": "user_create",
                    "extra": {"user_id": user.id, "phone_suffix": phone[-4:], "email": email},
                }
            },
        )
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
        logger.info(
            "User updated",
            extra={
                "details": {
                    "event": "user_update",
                    "extra": {"user_id": user.id, "fields": [field for field, value in kwargs.items() if value is not None]},
                }
            },
        )
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()
        logger.warning(
            "User deleted",
            extra={"details": {"event": "user_delete", "extra": {"user_id": user.id}}},
        )
