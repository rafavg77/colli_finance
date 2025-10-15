from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    income = Column(Numeric(12, 2), nullable=False, default=0)
    expenses = Column(Numeric(12, 2), nullable=False, default=0)
    executed = Column(Boolean, nullable=False, default=False)

    user = relationship("User", backref="transactions")
    card = relationship("Card", backref="transactions")
    category = relationship("Category", backref="transactions")
