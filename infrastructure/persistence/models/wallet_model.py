from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core.database import Base

if TYPE_CHECKING:
    from infrastructure.persistence.models.user_model import UserModel
    from infrastructure.persistence.models.wallet_asset import WalletAssetModel
    from infrastructure.persistence.models.transaction_model import TransactionModel
    from infrastructure.persistence.models.order_model import OrderModel


class WalletModel(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    fiat_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), default=Decimal("0.00000000"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["UserModel"] = relationship("UserModel", backref="wallet")

    assets: Mapped[List["WalletAssetModel"]] = relationship(
        "WalletAssetModel", back_populates="wallet", cascade="all, delete-orphan"
    )

    transactions: Mapped[List["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="wallet", cascade="all, delete-orphan"
    )
