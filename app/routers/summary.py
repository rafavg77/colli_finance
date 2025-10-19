from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.card import CardCRUD
from app.crud.transaction import TransactionCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.summary import CardSummary

router = APIRouter(prefix="/summary", tags=["summary"])


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido") from exc


@router.get("/cards", response_model=list[CardSummary])
async def card_summary(
    user_id: int = Query(..., description="ID del usuario"),
    start_date: str = Query(..., description="Fecha inicio en formato ISO"),
    end_date: str = Query(..., description="Fecha fin en formato ISO"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado para consultar este usuario")
    start = parse_date(start_date)
    end = parse_date(end_date)
    if start > end:
        raise HTTPException(status_code=400, detail="La fecha inicio debe ser menor o igual a la fecha fin")

    cards = await CardCRUD.list_by_user(db, current_user.id)
    # Work with operation_date (DATE); make the upper bound exclusive by advancing a day
    start_bound = start.date()
    end_bound = end.date() + timedelta(days=1)
    summary = await TransactionCRUD.summarize_by_card(db, current_user.id, start_bound, end_bound)
    summary_map = {item["card_id"]: item for item in summary}

    response: list[CardSummary] = []
    for card in cards:
        data = summary_map.get(card.id)
        income_total = Decimal(str(data["income_total"])) if data else Decimal("0.00")
        expenses_total = Decimal(str(data["expenses_total"])) if data else Decimal("0.00")
        balance = income_total - expenses_total
        bank_display = None
        bank_id = None
        if data:
            bank_display = data.get("bank_display_name")
            bank_id = data.get("bank_id")
        if bank_display is None and card.bank is not None:
            bank_display = card.bank.display_name
            bank_id = card.bank.id
        if bank_display is None:
            bank_display = card.bank_name
        if bank_id is None:
            bank_id = card.bank_id
        response.append(
            CardSummary(
                card_id=card.id,
                card_name=card.card_name,
                bank_id=bank_id,
                bank_name=bank_display,
                income_total=income_total,
                expenses_total=expenses_total,
                balance=balance,
            )
        )
    return response
