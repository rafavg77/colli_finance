from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="RESTRICT"), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    card_name = Column(String(100), nullable=False)
    alias = Column(String(100), nullable=True)
    billing_cycle_day = Column(SmallInteger, nullable=True)
    payment_due_day = Column(SmallInteger, nullable=True)
    grace_days = Column(SmallInteger, nullable=True)

    user = relationship("User", backref="cards")
    bank = relationship("Bank", back_populates="cards")
