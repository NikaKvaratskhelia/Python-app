import logging
import time
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from services.market_service import MarketService
from services.wallet_service import WalletService
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.transaction_model import TransactionModel

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
            .options(joinedload(OrderModel.wallet).joinedload(WalletModel.assets))
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
                if order.is_reserved:
                    price_diff = (order.target_price - current_price) * amount
                    if price_diff > 0:
                        order.wallet.fiat_balance += price_diff

                    asset = next(
                        (a for a in order.wallet.assets if a.symbol == symbol), None
                    )
                    if asset:
                        total_cost = (asset.amount * asset.average_buy_price) + (
                            amount * current_price
                        )
                        asset.amount += amount
                        asset.average_buy_price = total_cost / asset.amount
                    else:
                        new_asset = WalletAssetModel(
                            wallet_id=order.wallet_id,
                            symbol=symbol,
                            amount=amount,
                            average_buy_price=current_price,
                        )
                        db.add(new_asset)

                    tx = TransactionModel(
                        wallet_id=order.wallet_id,
                        type="BUY",
                        amount=amount,
                        price=current_price,
                        symbol=symbol,
                    )
                    db.add(tx)
                    order.status = "EXECUTED"
                    db.commit()
                    logger.info(
                        f"BUY ორდერი შესრულდა: {symbol} @ ${current_price}"
                    )
                else:
                    res = wallet_service.buy_asset(
                        user_id, symbol, amount, current_price
                    )
                    if res.is_success:
                        order.status = "EXECUTED"
                        db.commit()
                        logger.info(
                            f"BUY ორდერი შესრულდა: {symbol} @ ${current_price}"
                        )
                    else:
                        logger.warning(
                            f"BUY ორდერის შეცდომა (#{order.id}): {res.error}"
                        )

            # SELL LIMIT: საბაზრო ფასი >= სამიზნე ფასზე
            elif (
                order.order_type == "SELL_LIMIT"
                and current_price >= order.target_price
            ):
                if order.is_reserved:
                    proceeds = amount * current_price
                    order.wallet.fiat_balance += proceeds
                    tx = TransactionModel(
                        wallet_id=order.wallet_id,
                        type=order.order_type,
                        amount=amount,
                        price=current_price,
                        symbol=symbol,
                    )
                    db.add(tx)
                    order.status = "EXECUTED"
                    db.commit()
                    logger.info(
                        f"{order.order_type} ორდერი შესრულდა: {symbol} @ ${current_price}"
                    )
                else:
                    res = wallet_service.sell_asset(
                        user_id, symbol, amount, current_price
                    )
                    if res.is_success:
                        order.status = "EXECUTED"
                        db.commit()
                        logger.info(
                            f"{order.order_type} ორდერი შესრულდა: {symbol} @ ${current_price}"
                        )
                    else:
                        logger.warning(
                            f"{order.order_type} ორდერის შეცდომა (#{order.id}): {res.error}"
                        )

            # STOP LOSS: საბაზრო ფასი <= სამიზნე ფასზე
            elif (
                order.order_type == "STOP_LOSS"
                and current_price <= order.target_price
            ):
                if order.is_reserved:
                    proceeds = amount * current_price
                    order.wallet.fiat_balance += proceeds
                    tx = TransactionModel(
                        wallet_id=order.wallet_id,
                        type="STOP_LOSS",
                        amount=amount,
                        price=current_price,
                        symbol=symbol,
                    )
                    db.add(tx)
                    order.status = "EXECUTED"
                    db.commit()
                    logger.info(
                        f"STOP_LOSS ორდერი შესრულდა: {symbol} @ ${current_price}"
                    )
                else:
                    res = wallet_service.sell_asset(
                        user_id, symbol, amount, current_price
                    )
                    if res.is_success:
                        order.status = "EXECUTED"
                        db.commit()
                        logger.info(
                            f"STOP_LOSS ორდერი შესრულდა: {symbol} @ ${current_price}"
                        )
                    else:
                        logger.warning(
                            f"STOP_LOSS ორდერის შეცდომა (#{order.id}): {res.error}"
                        )

    @classmethod
    def run_bot(cls, interval_seconds: int = 15) -> None:
        """
        მუშაობს ფონურ ციკლში მითითებული ინტერვალით.
        """
        cls._running = True
        logger.info(
            f"კრიპტო ორდერების ბოტი ჩაირთო ({interval_seconds} წმ ინტერვალით)..."
        )

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
