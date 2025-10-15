from decimal import Decimal
from pydantic import BaseModel


class CardSummary(BaseModel):
    card_id: int
    card_name: str
    bank_name: str
    income_total: Decimal
    expenses_total: Decimal
    balance: Decimal
