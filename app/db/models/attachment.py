from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Link to a single transaction or to a transfer group (pair of transactions sharing transfer_id)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    transfer_id = Column(Integer, nullable=True, index=True)

    filename = Column(String(255), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    path = Column(Text, nullable=False)  # relative path from upload root

    user = relationship("User", backref="attachments")
    transaction = relationship("Transaction", backref="attachments")
