from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.card import CardCRUD
from app.crud.transaction import TransactionCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services.audit import register_audit

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = await TransactionCRUD.list_by_user(db, current_user.id)
    return transactions


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    card = await CardCRUD.get_by_id(db, payload.card_id, current_user.id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")
    transaction = await TransactionCRUD.create(db, current_user.id, **payload.dict())
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="transaction",
        details={"transaction_id": transaction.id},
    )
    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionCRUD.get_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionCRUD.get_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    if payload.card_id is not None and payload.card_id != transaction.card_id:
        card = await CardCRUD.get_by_id(db, payload.card_id, current_user.id)
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")
    updated = await TransactionCRUD.update(db, transaction, **payload.dict(exclude_unset=True))
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="transaction",
        details={"transaction_id": updated.id},
    )
    return updated


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = await TransactionCRUD.get_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    await TransactionCRUD.delete(db, transaction)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="transaction",
        details={"transaction_id": transaction_id},
    )
    return None
