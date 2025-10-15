from pydantic import BaseModel
from datetime import datetime


class AttachmentBase(BaseModel):
    filename: str
    content_type: str | None = None
    size: int | None = None


class AttachmentCreate(AttachmentBase):
    transaction_id: int | None = None
    transfer_id: int | None = None


class AttachmentResponse(AttachmentBase):
    id: int
    user_id: int
    transaction_id: int | None = None
    transfer_id: int | None = None
    path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
