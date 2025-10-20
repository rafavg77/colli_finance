from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.listener import ListenerCredCRUD, ListenerTemplateCRUD, ListenerConfigCRUD
from app.crud.bank import BankCRUD
from app.crud.card import CardCRUD
from app.db.models import User, ListenerCred, ListenerTemplate, ListenerConfig
from app.db.session import get_db
from app.schemas.listener import (
    ListenerCredCreate,
    ListenerCredUpdate,
    ListenerCredResponse,
    ListenerTemplateCreate,
    ListenerTemplateUpdate,
    ListenerTemplateResponse,
    ListenerConfigCreate,
    ListenerConfigUpdate,
    ListenerConfigResponse,
)
from app.services.audit import register_audit

router = APIRouter(prefix="/listener", tags=["listener"])


# Listener Credentials endpoints
@router.get("/credentials", response_model=ListenerCredResponse | None)
async def get_my_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's listener credentials"""
    cred = await ListenerCredCRUD.get_by_user(db, current_user.id)
    return cred


@router.post("/credentials", response_model=ListenerCredResponse, status_code=status.HTTP_201_CREATED)
async def create_credentials(
    payload: ListenerCredCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create listener credentials for current user"""
    existing = await ListenerCredCRUD.get_by_user(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las credenciales ya existen para este usuario"
        )
    
    cred = await ListenerCredCRUD.create(db, user_id=current_user.id, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="listener_cred",
        details={"cred_id": cred.id},
    )
    return cred


@router.patch("/credentials", response_model=ListenerCredResponse)
async def update_credentials(
    payload: ListenerCredUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's listener credentials"""
    cred = await ListenerCredCRUD.get_by_user(db, current_user.id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credenciales no encontradas"
        )
    
    update_data = payload.dict(exclude_unset=True)
    updated = await ListenerCredCRUD.update(db, cred, **update_data)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="listener_cred",
        details={"cred_id": cred.id},
    )
    return updated


@router.delete("/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete current user's listener credentials"""
    cred = await ListenerCredCRUD.get_by_user(db, current_user.id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credenciales no encontradas"
        )
    
    await ListenerCredCRUD.delete(db, cred)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="listener_cred",
        details={"cred_id": cred.id},
    )
    return None


# Listener Templates endpoints (admin-oriented)
@router.get("/templates", response_model=list[ListenerTemplateResponse])
async def list_templates(
    bank_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all listener templates, optionally filtered by bank"""
    if bank_id:
        templates = await ListenerTemplateCRUD.list_by_bank(db, bank_id)
    else:
        templates = await ListenerTemplateCRUD.list_all(db)
    return templates


@router.post("/templates", response_model=ListenerTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: ListenerTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a listener template"""
    # Verify bank exists
    bank = await BankCRUD.get_by_id(db, payload.bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Banco inválido"
        )
    
    # Check for duplicate
    existing = await ListenerTemplateCRUD.get_by_bank_and_code(
        db, payload.bank_id, payload.template_code
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una plantilla con este código para el banco"
        )
    
    template = await ListenerTemplateCRUD.create(db, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="listener_template",
        details={"template_id": template.id},
    )
    return template


@router.get("/templates/{template_id}", response_model=ListenerTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a specific listener template"""
    template = await ListenerTemplateCRUD.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )
    return template


@router.patch("/templates/{template_id}", response_model=ListenerTemplateResponse)
async def update_template(
    template_id: int,
    payload: ListenerTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a listener template"""
    template = await db.get(ListenerTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )
    
    update_data = payload.dict(exclude_unset=True)
    
    # Check for duplicate if bank_id or template_code changed
    if "bank_id" in update_data or "template_code" in update_data:
        new_bank_id = update_data.get("bank_id", template.bank_id)
        new_code = update_data.get("template_code", template.template_code)
        
        if new_bank_id != template.bank_id or new_code != template.template_code:
            existing = await ListenerTemplateCRUD.get_by_bank_and_code(db, new_bank_id, new_code)
            if existing and existing.id != template_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una plantilla con este código para el banco"
                )
    
    updated = await ListenerTemplateCRUD.update(db, template, **update_data)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="listener_template",
        details={"template_id": template_id},
    )
    return updated


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a listener template"""
    template = await db.get(ListenerTemplate, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla no encontrada"
        )
    
    await ListenerTemplateCRUD.delete(db, template)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="listener_template",
        details={"template_id": template_id},
    )
    return None


# Listener Configurations endpoints
@router.get("/configs", response_model=list[ListenerConfigResponse])
async def list_configs(
    card_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all listener configurations, optionally filtered by card"""
    if card_id:
        configs = await ListenerConfigCRUD.list_by_card(db, card_id)
    else:
        configs = await ListenerConfigCRUD.list_all(db)
    return configs


@router.post("/configs", response_model=ListenerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    payload: ListenerConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a listener configuration"""
    # Verify credential exists
    cred = await ListenerCredCRUD.get_by_id(db, payload.listener_cred_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credencial inválida"
        )
    
    # Verify template exists
    template = await ListenerTemplateCRUD.get_by_id(db, payload.listener_template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plantilla inválida"
        )
    
    # Verify card exists and belongs to the credential's user
    card = await CardCRUD.get_by_id(db, payload.card_id, cred.user_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tarjeta inválida o no pertenece al usuario"
        )
    
    # Check for duplicate
    existing = await ListenerConfigCRUD.get_by_binding(
        db,
        payload.listener_cred_id,
        payload.listener_template_id,
        payload.card_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe esta configuración"
        )
    
    config = await ListenerConfigCRUD.create(db, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="listener_config",
        details={"config_id": config.id},
    )
    return config


@router.get("/configs/{config_id}", response_model=ListenerConfigResponse)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a specific listener configuration"""
    config = await ListenerConfigCRUD.get_by_id(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    return config


@router.patch("/configs/{config_id}", response_model=ListenerConfigResponse)
async def update_config(
    config_id: int,
    payload: ListenerConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a listener configuration"""
    config = await db.get(ListenerConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    update_data = payload.dict(exclude_unset=True)
    
    # If any binding field changes, check for duplicate
    if any(field in update_data for field in ["listener_cred_id", "listener_template_id", "card_id"]):
        new_cred_id = update_data.get("listener_cred_id", config.listener_cred_id)
        new_template_id = update_data.get("listener_template_id", config.listener_template_id)
        new_card_id = update_data.get("card_id", config.card_id)
        
        if (new_cred_id != config.listener_cred_id or 
            new_template_id != config.listener_template_id or 
            new_card_id != config.card_id):
            existing = await ListenerConfigCRUD.get_by_binding(
                db, new_cred_id, new_template_id, new_card_id
            )
            if existing and existing.id != config_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe esta configuración"
                )
    
    updated = await ListenerConfigCRUD.update(db, config, **update_data)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="listener_config",
        details={"config_id": config_id},
    )
    return updated


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a listener configuration"""
    config = await db.get(ListenerConfig, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    await ListenerConfigCRUD.delete(db, config)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="listener_config",
        details={"config_id": config_id},
    )
    return None
