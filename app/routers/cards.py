from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.bank import BankCRUD
from app.crud.card import CardCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.card import CardCreate, CardResponse, CardUpdate
from app.services.audit import register_audit

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=list[CardResponse])
async def list_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cards = await CardCRUD.list_by_user(db, current_user.id)
    return cards


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    payload: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bank = await BankCRUD.get_by_id(db, payload.bank_id)
    if not bank or not bank.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Banco inválido o inactivo")

    card = await CardCRUD.create(db, current_user.id, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="card",
        details={"card_id": card.id},
    )
    return card


@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await CardCRUD.get_by_id(db, card_id, current_user.id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")
    return card


@router.patch("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    payload: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await CardCRUD.get_by_id(db, card_id, current_user.id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")

    update_data = payload.dict(exclude_unset=True)

    if "bank_id" in update_data:
        bank = await BankCRUD.get_by_id(db, update_data["bank_id"])
        if not bank or not bank.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Banco inválido o inactivo")

    target_type = update_data.get("type", card.type)
    billing = update_data.get("billing_cycle_day", card.billing_cycle_day)
    due = update_data.get("payment_due_day", card.payment_due_day)
    if target_type == "credit" and (billing is None or due is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las tarjetas de crédito requieren billing_cycle_day y payment_due_day",
        )

    updated = await CardCRUD.update(db, card, **update_data)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="card",
        details={"card_id": updated.id},
    )
    return updated


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await CardCRUD.get_by_id(db, card_id, current_user.id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")
    await CardCRUD.delete(db, card)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="card",
        details={"card_id": card_id},
    )
    return None
