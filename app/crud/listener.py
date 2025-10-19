from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ListenerCred, ListenerTemplate, ListenerConfig
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ListenerCredCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, cred_id: int) -> ListenerCred | None:
        result = await db.execute(select(ListenerCred).where(ListenerCred.id == cred_id))
        cred = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener cred by id",
            extra={"details": {"event": "listener_cred_lookup", "extra": {"cred_id": cred_id, "found": bool(cred)}}},
        )
        return cred

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> ListenerCred | None:
        result = await db.execute(select(ListenerCred).where(ListenerCred.user_id == user_id))
        cred = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener cred by user",
            extra={"details": {"event": "listener_cred_lookup_user", "extra": {"user_id": user_id, "found": bool(cred)}}},
        )
        return cred

    @staticmethod
    async def list_all(db: AsyncSession) -> list[ListenerCred]:
        result = await db.execute(select(ListenerCred))
        creds = list(result.scalars().all())
        logger.debug(
            "Listed listener creds",
            extra={"details": {"event": "listener_cred_list", "extra": {"count": len(creds)}}},
        )
        return creds

    @staticmethod
    async def create(db: AsyncSession, user_id: int, **kwargs) -> ListenerCred:
        cred = ListenerCred(user_id=user_id, **kwargs)
        db.add(cred)
        await db.commit()
        await db.refresh(cred)
        logger.info(
            "Listener cred created",
            extra={"details": {"event": "listener_cred_create", "extra": {"cred_id": cred.id, "user_id": user_id}}},
        )
        return cred

    @staticmethod
    async def update(db: AsyncSession, cred: ListenerCred, **kwargs) -> ListenerCred:
        for field, value in kwargs.items():
            if value is not None or field in ["google_credentials", "google_access_token"]:
                setattr(cred, field, value)
        await db.commit()
        await db.refresh(cred)
        logger.info(
            "Listener cred updated",
            extra={"details": {"event": "listener_cred_update", "extra": {"cred_id": cred.id}}},
        )
        return cred

    @staticmethod
    async def delete(db: AsyncSession, cred: ListenerCred) -> None:
        await db.delete(cred)
        await db.commit()
        logger.warning(
            "Listener cred deleted",
            extra={"details": {"event": "listener_cred_delete", "extra": {"cred_id": cred.id}}},
        )


class ListenerTemplateCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, template_id: int) -> ListenerTemplate | None:
        result = await db.execute(select(ListenerTemplate).where(ListenerTemplate.id == template_id))
        template = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener template by id",
            extra={"details": {"event": "listener_template_lookup", "extra": {"template_id": template_id, "found": bool(template)}}},
        )
        return template

    @staticmethod
    async def get_by_bank_and_code(db: AsyncSession, bank_id: int, template_code: str) -> ListenerTemplate | None:
        result = await db.execute(
            select(ListenerTemplate).where(
                ListenerTemplate.bank_id == bank_id,
                ListenerTemplate.template_code == template_code
            )
        )
        template = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener template by bank and code",
            extra={"details": {"event": "listener_template_lookup_bank_code", "extra": {"bank_id": bank_id, "template_code": template_code, "found": bool(template)}}},
        )
        return template

    @staticmethod
    async def list_by_bank(db: AsyncSession, bank_id: int) -> list[ListenerTemplate]:
        result = await db.execute(
            select(ListenerTemplate).where(ListenerTemplate.bank_id == bank_id)
        )
        templates = list(result.scalars().all())
        logger.debug(
            "Listed listener templates by bank",
            extra={"details": {"event": "listener_template_list_bank", "extra": {"bank_id": bank_id, "count": len(templates)}}},
        )
        return templates

    @staticmethod
    async def list_all(db: AsyncSession) -> list[ListenerTemplate]:
        result = await db.execute(select(ListenerTemplate))
        templates = list(result.scalars().all())
        logger.debug(
            "Listed all listener templates",
            extra={"details": {"event": "listener_template_list", "extra": {"count": len(templates)}}},
        )
        return templates

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> ListenerTemplate:
        template = ListenerTemplate(**kwargs)
        db.add(template)
        await db.commit()
        await db.refresh(template)
        logger.info(
            "Listener template created",
            extra={"details": {"event": "listener_template_create", "extra": {"template_id": template.id, "bank_id": template.bank_id}}},
        )
        return template

    @staticmethod
    async def update(db: AsyncSession, template: ListenerTemplate, **kwargs) -> ListenerTemplate:
        for field, value in kwargs.items():
            if value is not None or field in ["subject_pattern", "amount_pattern", "description_pattern", "date_pattern", "time_pattern", "template_metadata"]:
                setattr(template, field, value)
        await db.commit()
        await db.refresh(template)
        logger.info(
            "Listener template updated",
            extra={"details": {"event": "listener_template_update", "extra": {"template_id": template.id}}},
        )
        return template

    @staticmethod
    async def delete(db: AsyncSession, template: ListenerTemplate) -> None:
        await db.delete(template)
        await db.commit()
        logger.warning(
            "Listener template deleted",
            extra={"details": {"event": "listener_template_delete", "extra": {"template_id": template.id}}},
        )


class ListenerConfigCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, config_id: int) -> ListenerConfig | None:
        result = await db.execute(select(ListenerConfig).where(ListenerConfig.id == config_id))
        config = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener config by id",
            extra={"details": {"event": "listener_config_lookup", "extra": {"config_id": config_id, "found": bool(config)}}},
        )
        return config

    @staticmethod
    async def get_by_binding(
        db: AsyncSession, 
        listener_cred_id: int, 
        listener_template_id: int, 
        card_id: int
    ) -> ListenerConfig | None:
        result = await db.execute(
            select(ListenerConfig).where(
                ListenerConfig.listener_cred_id == listener_cred_id,
                ListenerConfig.listener_template_id == listener_template_id,
                ListenerConfig.card_id == card_id
            )
        )
        config = result.scalar_one_or_none()
        logger.debug(
            "Fetched listener config by binding",
            extra={"details": {"event": "listener_config_lookup_binding", "extra": {"found": bool(config)}}},
        )
        return config

    @staticmethod
    async def list_by_card(db: AsyncSession, card_id: int) -> list[ListenerConfig]:
        result = await db.execute(
            select(ListenerConfig).where(ListenerConfig.card_id == card_id)
        )
        configs = list(result.scalars().all())
        logger.debug(
            "Listed listener configs by card",
            extra={"details": {"event": "listener_config_list_card", "extra": {"card_id": card_id, "count": len(configs)}}},
        )
        return configs

    @staticmethod
    async def list_all(db: AsyncSession) -> list[ListenerConfig]:
        result = await db.execute(select(ListenerConfig))
        configs = list(result.scalars().all())
        logger.debug(
            "Listed all listener configs",
            extra={"details": {"event": "listener_config_list", "extra": {"count": len(configs)}}},
        )
        return configs

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> ListenerConfig:
        config = ListenerConfig(**kwargs)
        db.add(config)
        await db.commit()
        await db.refresh(config)
        logger.info(
            "Listener config created",
            extra={"details": {"event": "listener_config_create", "extra": {"config_id": config.id}}},
        )
        return config

    @staticmethod
    async def update(db: AsyncSession, config: ListenerConfig, **kwargs) -> ListenerConfig:
        for field, value in kwargs.items():
            if value is not None:
                setattr(config, field, value)
        await db.commit()
        await db.refresh(config)
        logger.info(
            "Listener config updated",
            extra={"details": {"event": "listener_config_update", "extra": {"config_id": config.id}}},
        )
        return config

    @staticmethod
    async def delete(db: AsyncSession, config: ListenerConfig) -> None:
        await db.delete(config)
        await db.commit()
        logger.warning(
            "Listener config deleted",
            extra={"details": {"event": "listener_config_delete", "extra": {"config_id": config.id}}},
        )
