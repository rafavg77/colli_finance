from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category


class CategoryCRUD:
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Category | None:
        result = await db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Category]:
        result = await db.execute(select(Category))
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, *, name: str) -> Category:
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(db: AsyncSession, category: Category, *, name: str | None = None) -> Category:
        if name is not None:
            category.name = name
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category: Category) -> None:
        await db.delete(category)
        await db.commit()
