from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from unittest.mock import Base
from core.database import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    wallet_id = Column(
        Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )

    type = Column(String(20), nullable=False)
    symbol = Column(String(10), nullable=True)
    amount = Column(Numeric(precision=18, scale=8), nullable=False)
    price = Column(Numeric(precision=18, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("WalletModel", back_populates="transactions")
