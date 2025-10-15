from collections import defaultdict
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.card import CardCRUD
from app.crud.category import CategoryCRUD
from app.crud.transaction import TransactionCRUD
from app.db.models import Transaction, User
from app.db.session import get_db
from app.schemas.transfer import TransferRequest, TransferResponse, TransferTransaction
from app.core.logging_config import get_logger
from app.services.audit import register_audit

logger = get_logger(__name__)

router = APIRouter(prefix="/transfers", tags=["transfers"])


async def _get_card_balance(db: AsyncSession, user_id: int, card_id: int) -> Decimal:
    stmt = select(
        func.coalesce(func.sum(Transaction.income), 0) - func.coalesce(func.sum(Transaction.expenses), 0)
    ).where(Transaction.user_id == user_id, Transaction.card_id == card_id)
    result = await db.execute(stmt)
    balance = result.scalar() or 0
    return Decimal(str(balance))


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify both cards belong to the current user
    src = await CardCRUD.get_by_id(db, payload.source_card_id, current_user.id)
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta origen no encontrada")
    dst = await CardCRUD.get_by_id(db, payload.destination_card_id, current_user.id)
    if not dst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta destino no encontrada")
    if payload.source_card_id == payload.destination_card_id:
        raise HTTPException(status_code=400, detail="La tarjeta origen y destino no pueden ser la misma")

    # Validate category id if provided
    if payload.category_id is not None:
        if await CategoryCRUD.get_by_id(db, payload.category_id) is None:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Validate balance on source card
    balance = await _get_card_balance(db, current_user.id, payload.source_card_id)
    amount = payload.amount.quantize(Decimal("0.01"))
    if balance < amount:
        logger.warning(
            "Insufficient funds for transfer",
            extra={
                "details": {
                    "event": "transfer_insufficient_funds",
                    "extra": {"user_id": current_user.id, "card_id": payload.source_card_id, "balance": str(balance), "attempt": str(amount)},
                }
            },
        )
        raise HTTPException(status_code=400, detail="Fondos insuficientes en la tarjeta origen")

    # Perform transfer
    expense_tx, income_tx = await TransactionCRUD.transfer(
        db,
        user_id=current_user.id,
        source_card_id=payload.source_card_id,
        destination_card_id=payload.destination_card_id,
        amount=amount,
        description=payload.description,
        category_id=payload.category_id,
    )

    # Register audit
    await register_audit(
        db,
        user_id=current_user.id,
        action="transfer",
        resource="transaction",
        details={
            "source_card_id": payload.source_card_id,
            "destination_card_id": payload.destination_card_id,
            "amount": str(amount),
            "transfer_id": expense_tx.transfer_id,
            "expense_tx": expense_tx.id,
            "income_tx": income_tx.id,
        },
    )

    logger.info(
        "Transfer requested",
        extra={
            "details": {
                "event": "transfer_request",
                "extra": {
                    "user_id": current_user.id,
                    "source_card_id": payload.source_card_id,
                    "destination_card_id": payload.destination_card_id,
                    "amount": str(amount),
                },
            }
        },
    )

    return TransferResponse(
        source_transaction=TransferTransaction.model_validate(expense_tx),
        destination_transaction=TransferTransaction.model_validate(income_tx),
    )


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # fetch both transactions belonging to this transfer and user
    stmt = select(Transaction).where(
        and_(Transaction.user_id == current_user.id, Transaction.transfer_id == transfer_id)
    )
    result = await db.execute(stmt)
    txs = list(result.scalars().all())
    if not txs:
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")
    if len(txs) != 2:
        logger.warning(
            "Unexpected transfer size",
            extra={"details": {"event": "transfer_read_incomplete", "extra": {"transfer_id": transfer_id, "count": len(txs)}}},
        )
    # Try to pick expense as source and income as destination
    source_tx = next((t for t in txs if Decimal(str(t.expenses)) > 0), txs[0])
    destination_tx = next((t for t in txs if Decimal(str(t.income)) > 0 and t is not source_tx), txs[-1])
    return TransferResponse(
        source_transaction=TransferTransaction.model_validate(source_tx),
        destination_transaction=TransferTransaction.model_validate(destination_tx),
    )


@router.get("", response_model=list[TransferResponse])
async def list_transfers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get page of transfer_ids ordered by latest created_at
    ids_stmt = (
        select(Transaction.transfer_id)
        .where(and_(Transaction.user_id == current_user.id, Transaction.transfer_id.is_not(None)))
        .group_by(Transaction.transfer_id)
        .order_by(func.max(Transaction.created_at).desc())
        .limit(limit)
        .offset(offset)
    )
    ids_result = await db.execute(ids_stmt)
    transfer_ids = [row[0] for row in ids_result.all()]
    if not transfer_ids:
        return []

    # Fetch all transactions for those transfer_ids
    tx_stmt = select(Transaction).where(
        and_(Transaction.user_id == current_user.id, Transaction.transfer_id.in_(transfer_ids))
    )
    tx_result = await db.execute(tx_stmt)
    txs = list(tx_result.scalars().all())

    grouped: dict[int, list[Transaction]] = defaultdict(list)
    for t in txs:
        if t.transfer_id is not None:
            grouped[int(t.transfer_id)].append(t)

    responses: list[TransferResponse] = []
    for tid in transfer_ids:
        pair = grouped.get(int(tid), [])
        if not pair:
            continue
        source_tx = next((t for t in pair if Decimal(str(t.expenses)) > 0), pair[0])
        destination_tx = next((t for t in pair if Decimal(str(t.income)) > 0 and t is not source_tx), pair[-1])
        responses.append(
            TransferResponse(
                source_transaction=TransferTransaction.model_validate(source_tx),
                destination_transaction=TransferTransaction.model_validate(destination_tx),
            )
        )
    return responses


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transfer(
    transfer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch both transactions for this transfer and user
    stmt = select(Transaction).where(
        and_(Transaction.user_id == current_user.id, Transaction.transfer_id == transfer_id)
    )
    result = await db.execute(stmt)
    txs = list(result.scalars().all())
    if not txs:
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")

    # Delete both
    for t in txs:
        await db.delete(t)
    await db.commit()

    await register_audit(
        db,
        user_id=current_user.id,
        action="transfer_delete",
        resource="transaction",
        details={"transfer_id": transfer_id, "count": len(txs)},
    )
    return None


@router.patch("/{transfer_id}", response_model=TransferResponse)
async def update_transfer(
    transfer_id: int,
    description: str | None = None,
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate category if provided
    if category_id is not None:
        if await CategoryCRUD.get_by_id(db, category_id) is None:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    stmt = select(Transaction).where(
        and_(Transaction.user_id == current_user.id, Transaction.transfer_id == transfer_id)
    )
    result = await db.execute(stmt)
    txs = list(result.scalars().all())
    if not txs:
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")

    # Update both transactions
    changed = False
    for t in txs:
        if description is not None:
            t.description = description
            changed = True
        if category_id is not None:
            t.category_id = category_id
            changed = True
    if changed:
        await db.commit()
        # refresh any two to return
        for t in txs:
            await db.refresh(t)

        await register_audit(
            db,
            user_id=current_user.id,
            action="transfer_update",
            resource="transaction",
            details={"transfer_id": transfer_id, "updated_description": bool(description), "updated_category": bool(category_id)},
        )

    # Respond with the pair (source/destination heuristic)
    source_tx = next((t for t in txs if Decimal(str(t.expenses)) > 0), txs[0])
    destination_tx = next((t for t in txs if Decimal(str(t.income)) > 0 and t is not source_tx), txs[-1])
    return TransferResponse(
        source_transaction=TransferTransaction.model_validate(source_tx),
        destination_transaction=TransferTransaction.model_validate(destination_tx),
    )
