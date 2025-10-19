from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.bank import BankCRUD
from app.db.models import Bank, User
from app.db.session import get_db
from app.schemas.bank import BankBase, BankResponse
from app.services.audit import register_audit

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=list[BankResponse])
async def list_banks(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    banks = await BankCRUD.list_active(db)
    return banks


@router.post("", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
async def create_bank(
    payload: BankBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await BankCRUD.get_by_slug(db, payload.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El banco ya existe")
    bank = await BankCRUD.create(db, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="bank",
        details={"bank_id": bank.id},
    )
    return bank


@router.get("/{bank_id}", response_model=BankResponse)
async def get_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    bank = await BankCRUD.get_by_id(db, bank_id)
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco no encontrado")
    return bank


@router.patch("/{bank_id}", response_model=BankResponse)
async def update_bank(
    bank_id: int,
    payload: BankBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await db.get(Bank, bank_id)
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco no encontrado")
    
    update_data = payload.dict(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != bank.slug:
        existing = await BankCRUD.get_by_slug(db, update_data["slug"])
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El slug ya existe")
    
    updated = await BankCRUD.update(db, bank, **update_data)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="bank",
        details={"bank_id": bank_id},
    )
    return updated


@router.delete("/{bank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await db.get(Bank, bank_id)
    if not bank:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banco no encontrado")
    await BankCRUD.delete(db, bank)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="bank",
        details={"bank_id": bank_id},
    )
    return None
