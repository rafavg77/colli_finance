from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AuditResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource: str
    details: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
