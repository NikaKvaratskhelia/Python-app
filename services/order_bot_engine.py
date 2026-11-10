import logging
import time
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from services.market_service import MarketService
from services.wallet_service import WalletService
from infrastructure.persistence.models.order_model import OrderModel

logger = logging.getLogger(__name__)


class OrderBotEngine:
    _running: bool = False

    @staticmethod
    def check_orders_once(db: Optional[Session] = None) -> None:
        """
        ამოწმებს PENDING ორდერებს და ადარებს საბაზრო ფასებს ერთ ციკლში.
        """
        if db is not None:
            OrderBotEngine._process(db)
        else:
            with get_db() as session:
                OrderBotEngine._process(session)

    @staticmethod
    def _process(db: Session) -> None:
        pending_orders: list[OrderModel] = (
            db.query(OrderModel)
            .options(joinedload(OrderModel.wallet))
            .filter(OrderModel.status == "PENDING")
            .all()
        )

        if not pending_orders:
            return

        market_prices = MarketService.get_all_active_prices()
        if not market_prices:
            return

        wallet_service = WalletService(db)

        for order in pending_orders:
            symbol = order.symbol.strip().upper()
            market_info = market_prices.get(symbol)
            if not market_info:
                continue

            current_price: Decimal = market_info["price"]
            user_id: int = order.wallet.user_id
            amount = Decimal(str(order.amount))

            # BUY LIMIT: საბაზრო ფასი <= სამიზნე ფასზე
            if order.order_type == "BUY_LIMIT" and current_price <= order.target_price:
                res = wallet_service.buy_asset(user_id, symbol, amount, current_price)
                if res.is_success:
                    order.status = "EXECUTED"
                    db.commit()
                    logger.info(f"BUY ორდერი შესრულდა: {symbol} @ ${current_price}")
                else:
                    logger.warning(f"BUY ორდერის შეცდომა (#{order.id}): {res.error}")

            # SELL LIMIT: საბაზრო ფასი >= სამიზნე ფასზე
            elif order.order_type == "SELL_LIMIT" and current_price >= order.target_price:
                res = wallet_service.sell_asset(user_id, symbol, amount, current_price)
                if res.is_success:
                    order.status = "EXECUTED"
                    db.commit()
                    logger.info(f"SELL ორდერი შესრულდა: {symbol} @ ${current_price}")
                else:
                    logger.warning(f"SELL ორდერის შეცდომა (#{order.id}): {res.error}")

    @classmethod
    def run_bot(cls, interval_seconds: int = 15) -> None:
        """
        მუშაობს ფონურ ციკლში მითითებული ინტერვალით.
        """
        cls._running = True
        logger.info(f"კრიპტო ორდერების ბოტი ჩაირთო ({interval_seconds} წმ ინტერვალით)...")

        while cls._running:
            try:
                cls.check_orders_once()
            except Exception as e:
                logger.error(f"ბოტის შეცდომა: {e}")

            time.sleep(interval_seconds)

    @classmethod
    def stop(cls) -> None:
        """აჩერებს ბოტის ციკლს."""
        cls._running = False
