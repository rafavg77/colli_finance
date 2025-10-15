from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Audit


class AuditCRUD:
    @staticmethod
    async def list_logs(db: AsyncSession, user_id: int | None = None) -> list[Audit]:
        stmt = select(Audit)
        if user_id is not None:
            stmt = stmt.where(Audit.user_id == user_id)
        result = await db.execute(stmt.order_by(Audit.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        user_id: int | None,
        action: str,
        resource: str,
        details: dict | None = None,
    ) -> Audit:
        audit = Audit(user_id=user_id, action=action, resource=resource, details=details)
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit
