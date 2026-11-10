from decimal import Decimal
from unittest.mock import MagicMock

from domain.aggregates.user.entities.user import User
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.repositories.user_repository import UserRepository
from services.market_service import MarketService
from services.order_bot_engine import OrderBotEngine
from services.wallet_service import WalletService


def _create_user_and_wallet(db_session, username="bot_user", initial_fiat=Decimal("10000.00")):
    user_repo = UserRepository(db_session)
    user = User(username=username, password_hash="hash")
    user_repo.save(user)
    db_session.commit()
    user_model = db_session.query(UserModel).filter(UserModel.username == username).first()

    wallet_model = WalletModel(user_id=user_model.id, fiat_balance=initial_fiat)
    db_session.add(wallet_model)
    db_session.commit()
    return user_model, wallet_model


def test_buy_limit_executed_when_price_matches(db_session, monkeypatch):
    user, wallet = _create_user_and_wallet(db_session, "user_buy", Decimal("10000.00"))
    order = OrderModel(
        wallet_id=wallet.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        target_price=Decimal("50000.00"),
        amount=Decimal("0.1"),
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {"BTC": {"price": Decimal("49000.00"), "change": Decimal("1.0")}},
    )

    OrderBotEngine.check_orders_once(db_session)

    db_session.refresh(order)
    db_session.refresh(wallet)
    assert order.status == "EXECUTED"
    assert wallet.fiat_balance == Decimal("5100.00")  # 10000 - (0.1 * 49000)


def test_buy_limit_not_executed_when_price_higher(db_session, monkeypatch):
    _, wallet = _create_user_and_wallet(db_session, "user_skip")
    order = OrderModel(
        wallet_id=wallet.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        target_price=Decimal("50000.00"),
        amount=Decimal("0.1"),
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {"BTC": {"price": Decimal("52000.00"), "change": Decimal("1.0")}},
    )

    OrderBotEngine.check_orders_once(db_session)

    db_session.refresh(order)
    assert order.status == "PENDING"


def test_sell_limit_executed_when_price_matches(db_session, monkeypatch):
    user, wallet = _create_user_and_wallet(db_session, "user_sell", Decimal("10000.00"))

    # Buy 1 ETH first
    wallet_svc = WalletService(db_session)
    wallet_svc.buy_asset(user.id, "ETH", Decimal("1.0"), Decimal("2000.00"))
    db_session.commit()

    order = OrderModel(
        wallet_id=wallet.id,
        symbol="ETH",
        order_type="SELL_LIMIT",
        target_price=Decimal("3000.00"),
        amount=Decimal("1.0"),
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {"ETH": {"price": Decimal("3100.00"), "change": Decimal("5.0")}},
    )

    OrderBotEngine.check_orders_once(db_session)

    db_session.refresh(order)
    assert order.status == "EXECUTED"


def test_insufficient_funds_does_not_mark_executed(db_session, monkeypatch):
    """
    CRITICAL BUG FIX:
    When user has insufficient funds, order should NOT be marked EXECUTED.
    """
    _, wallet = _create_user_and_wallet(db_session, "user_poor", Decimal("10.00"))
    order = OrderModel(
        wallet_id=wallet.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        target_price=Decimal("50000.00"),
        amount=Decimal("1.0"),  # Costs $45,000, user only has $10
        status="PENDING",
    )
    db_session.add(order)
    db_session.commit()

    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {"BTC": {"price": Decimal("45000.00"), "change": Decimal("-2.0")}},
    )

    OrderBotEngine.check_orders_once(db_session)

    db_session.refresh(order)
    assert order.status == "PENDING"  # Remains PENDING, NOT EXECUTED!


def test_stop_bot():
    OrderBotEngine._running = True
    OrderBotEngine.stop()
    assert OrderBotEngine._running is False
