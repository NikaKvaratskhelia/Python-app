from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class WatchlistModel(Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uq_user_symbol_watchlist"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
