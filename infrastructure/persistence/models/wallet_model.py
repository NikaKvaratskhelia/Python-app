from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base


class WalletModel(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    fiat_balance = Column(
        Numeric(precision=18, scale=8), default=0.00000000, nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserModel", backref="wallet")

    assets = relationship(
        "WalletAssetModel", back_populates="wallet", cascade="all, delete-orphan"
    )

    transactions = relationship(
        "TransactionModel", back_populates="wallet", cascade="all, delete-orphan"
    )
