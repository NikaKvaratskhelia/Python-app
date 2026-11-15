from sqlalchemy.orm import Session
from core.result import Result
from infrastructure.persistence.models.watchlist_model import WatchlistModel


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db

    def add(self, user_id: int, symbol: str) -> Result[WatchlistModel, str]:
        symbol = symbol.strip().upper()
        if not symbol:
            return Result.failure("სიმბოლო არ შეიძლება იყოს ცარიელი.")

        existing = (
            self.db.query(WatchlistModel)
            .filter(
                WatchlistModel.user_id == user_id,
                WatchlistModel.symbol == symbol,
            )
            .first()
        )
        if existing:
            return Result.failure(f"{symbol} უკვე დამატებულია რჩეულებში.")

        item = WatchlistModel(user_id=user_id, symbol=symbol)
        self.db.add(item)
        self.db.flush()
        return Result.success(item)

    def remove(self, user_id: int, symbol: str) -> Result[None, str]:
        symbol = symbol.strip().upper()
        item = (
            self.db.query(WatchlistModel)
            .filter(
                WatchlistModel.user_id == user_id,
                WatchlistModel.symbol == symbol,
            )
            .first()
        )
        if not item:
            return Result.failure(f"{symbol} ვერ მოიძებნა რჩეულებში.")

        self.db.delete(item)
        self.db.flush()
        return Result.success(None)

    def get_watchlist(self, user_id: int) -> list[str]:
        items = (
            self.db.query(WatchlistModel)
            .filter(WatchlistModel.user_id == user_id)
            .order_by(WatchlistModel.id.asc())
            .all()
        )
        return [i.symbol for i in items]
