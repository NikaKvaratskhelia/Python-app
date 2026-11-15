from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class PriceAlertModel(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    target_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=8), nullable=False
    )
    condition: Mapped[str] = mapped_column(String(10), nullable=False)  # "ABOVE" or "BELOW"
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
