from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from pydantic import field_validator


class TransferRequest(BaseModel):
    source_card_id: int = Field(..., description="Card ID to transfer from")
    destination_card_id: int = Field(..., description="Card ID to transfer to")
    amount: Decimal = Field(..., gt=0, description="Amount to transfer (must be > 0)")
    description: str | None = Field(None, description="Optional description for both transactions")
    category_id: int | None = Field(None, description="Optional category ID to set on both transactions")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        # Ensure two decimal places max
        return v.quantize(Decimal("0.01"))


class TransferTransaction(BaseModel):
    id: int
    card_id: int
    description: str
    category_id: int | None
    income: Decimal
    expenses: Decimal
    executed: bool
    transfer_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransferResponse(BaseModel):
    source_transaction: TransferTransaction
    destination_transaction: TransferTransaction
