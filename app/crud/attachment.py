from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Attachment


class AttachmentCRUD:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        user_id: int,
        filename: str,
        path: str,
        content_type: str | None,
        size: int | None,
        transaction_id: int | None,
        transfer_id: int | None,
    ) -> Attachment:
        att = Attachment(
            user_id=user_id,
            filename=filename,
            path=path,
            content_type=content_type,
            size=size,
            transaction_id=transaction_id,
            transfer_id=transfer_id,
        )
        db.add(att)
        await db.commit()
        await db.refresh(att)
        return att

    @staticmethod
    async def list_by_transaction(db: AsyncSession, user_id: int, transaction_id: int) -> list[Attachment]:
        res = await db.execute(
            select(Attachment).where(Attachment.user_id == user_id, Attachment.transaction_id == transaction_id)
        )
        return list(res.scalars().all())

    @staticmethod
    async def list_by_transfer(db: AsyncSession, user_id: int, transfer_id: int) -> list[Attachment]:
        res = await db.execute(select(Attachment).where(Attachment.user_id == user_id, Attachment.transfer_id == transfer_id))
        return list(res.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int, attachment_id: int) -> Attachment | None:
        res = await db.execute(select(Attachment).where(Attachment.id == attachment_id, Attachment.user_id == user_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, attachment: Attachment) -> None:
        await db.delete(attachment)
        await db.commit()
