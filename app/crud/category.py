from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CategoryCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        logger.debug(
            "Fetched category by id",
            extra={"details": {"event": "category_lookup_id", "extra": {"id": category_id, "found": bool(category)}}},
        )
        return category
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Category | None:
        result = await db.execute(select(Category).where(Category.name == name))
        category = result.scalar_one_or_none()
        logger.debug(
            "Fetched category by name",
            extra={"details": {"event": "category_lookup", "extra": {"name": name, "found": bool(category)}}},
        )
        return category

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Category]:
        result = await db.execute(select(Category))
        categories = list(result.scalars().all())
        logger.debug(
            "Listed categories",
            extra={"details": {"event": "category_list", "extra": {"count": len(categories)}}},
        )
        return categories

    @staticmethod
    async def create(db: AsyncSession, *, name: str) -> Category:
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        logger.info(
            "Category created",
            extra={"details": {"event": "category_create", "extra": {"category_id": category.id, "name": name}}},
        )
        return category

    @staticmethod
    async def update(db: AsyncSession, category: Category, *, name: str | None = None) -> Category:
        if name is not None:
            category.name = name
        await db.commit()
        await db.refresh(category)
        logger.info(
            "Category updated",
            extra={"details": {"event": "category_update", "extra": {"category_id": category.id}}},
        )
        return category

    @staticmethod
    async def delete(db: AsyncSession, category: Category) -> None:
        await db.delete(category)
        await db.commit()
        logger.warning(
            "Category deleted",
            extra={"details": {"event": "category_delete", "extra": {"category_id": category.id}}},
        )
