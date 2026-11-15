from decimal import Decimal
from domain.aggregates.user.entities.user import User
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.repositories.user_repository import UserRepository
from services.order_service import OrderService
from services.wallet_service import WalletService


def _setup_user(db_session, username="order_test_user", initial_fiat=Decimal("10000.00")):
    user_repo = UserRepository(db_session)
    user = User(username=username, password_hash="hash")
    user_repo.save(user)
    db_session.commit()
    user_model = db_session.query(UserModel).filter(UserModel.username == username).first()

    wallet_model = WalletModel(user_id=user_model.id, fiat_balance=initial_fiat)
    db_session.add(wallet_model)
    db_session.commit()
    return user_model, wallet_model


def test_create_buy_limit_reserves_fiat(db_session):
    user, wallet = _setup_user(db_session, "user_res_buy", Decimal("5000.00"))
    order_svc = OrderService(db_session)

    res = order_svc.create_order(
        user_id=user.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        amount=Decimal("0.05"),
        target_price=Decimal("60000.00"),
    )

    assert res.is_success
    order = res.value
    assert order.status == "PENDING"
    assert order.is_reserved is True

    db_session.refresh(wallet)
    # 5000 - (0.05 * 60000 = 3000) = 2000
    assert wallet.fiat_balance == Decimal("2000.00")


def test_create_buy_limit_insufficient_fiat(db_session):
    user, wallet = _setup_user(db_session, "user_poor_buy", Decimal("500.00"))
    order_svc = OrderService(db_session)

    res = order_svc.create_order(
        user_id=user.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        amount=Decimal("0.1"),
        target_price=Decimal("60000.00"),  # Costs 6000
    )

    assert res.is_failure
    assert "არასაკმარისი ბალანსი" in res.error
    db_session.refresh(wallet)
    assert wallet.fiat_balance == Decimal("500.00")


def test_create_sell_limit_reserves_crypto(db_session):
    user, wallet = _setup_user(db_session, "user_res_sell", Decimal("10000.00"))
    wallet_svc = WalletService(db_session)
    wallet_svc.buy_asset(user.id, "SOL", Decimal("10.0"), Decimal("100.00"))
    db_session.commit()

    order_svc = OrderService(db_session)
    res = order_svc.create_order(
        user_id=user.id,
        symbol="SOL",
        order_type="SELL_LIMIT",
        amount=Decimal("4.0"),
        target_price=Decimal("200.00"),
    )

    assert res.is_success
    db_session.refresh(wallet)
    sol_asset = next(a for a in wallet.assets if a.symbol == "SOL")
    assert sol_asset.amount == Decimal("6.0")  # 10 - 4 = 6


def test_create_stop_loss_and_sell_limit_reserves_crypto(db_session):
    user, wallet = _setup_user(db_session, "user_sl_sell", Decimal("10000.00"))
    wallet_svc = WalletService(db_session)
    wallet_svc.buy_asset(user.id, "ETH", Decimal("5.0"), Decimal("2000.00"))
    db_session.commit()

    order_svc = OrderService(db_session)

    # Stop Loss for 2 ETH
    sl_res = order_svc.create_order(
        user_id=user.id,
        symbol="ETH",
        order_type="STOP_LOSS",
        amount=Decimal("2.0"),
        target_price=Decimal("1800.00"),
    )
    assert sl_res.is_success

    # Sell Limit for 2 ETH
    sell_res = order_svc.create_order(
        user_id=user.id,
        symbol="ETH",
        order_type="SELL_LIMIT",
        amount=Decimal("2.0"),
        target_price=Decimal("2500.00"),
    )
    assert sell_res.is_success

    # Remaining in wallet: 5 - 2 - 2 = 1 ETH
    db_session.refresh(wallet)
    eth_asset = next(a for a in wallet.assets if a.symbol == "ETH")
    assert eth_asset.amount == Decimal("1.0")

    # Try selling 2 more ETH -> Should fail because only 1 remains available
    fail_res = order_svc.create_order(
        user_id=user.id,
        symbol="ETH",
        order_type="SELL_LIMIT",
        amount=Decimal("2.0"),
        target_price=Decimal("3000.00"),
    )
    assert fail_res.is_failure
    assert "არასაკმარისი ETH აქტივი" in fail_res.error


def test_cancel_buy_order_refunds_fiat(db_session):
    user, wallet = _setup_user(db_session, "user_cancel_buy", Decimal("1000.00"))
    order_svc = OrderService(db_session)

    res = order_svc.create_order(
        user_id=user.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        amount=Decimal("0.01"),
        target_price=Decimal("50000.00"),  # 500
    )
    assert res.is_success
    order = res.value

    db_session.refresh(wallet)
    assert wallet.fiat_balance == Decimal("500.00")

    # Cancel order
    cancel_res = order_svc.cancel_order(order.id, user.id)
    assert cancel_res.is_success
    assert cancel_res.value.status == "CANCELLED"

    db_session.refresh(wallet)
    assert wallet.fiat_balance == Decimal("1000.00")


def test_cancel_sell_order_refunds_crypto(db_session):
    user, wallet = _setup_user(db_session, "user_cancel_sell", Decimal("5000.00"))
    wallet_svc = WalletService(db_session)
    wallet_svc.buy_asset(user.id, "DOT", Decimal("50.0"), Decimal("5.00"))
    db_session.commit()

    order_svc = OrderService(db_session)
    res = order_svc.create_order(
        user_id=user.id,
        symbol="DOT",
        order_type="SELL_LIMIT",
        amount=Decimal("20.0"),
        target_price=Decimal("10.00"),
    )
    assert res.is_success
    order = res.value

    db_session.refresh(wallet)
    dot_asset = next(a for a in wallet.assets if a.symbol == "DOT")
    assert dot_asset.amount == Decimal("30.0")

    # Cancel order
    cancel_res = order_svc.cancel_order(order.id, user.id)
    assert cancel_res.is_success

    db_session.refresh(wallet)
    dot_asset = next(a for a in wallet.assets if a.symbol == "DOT")
    assert dot_asset.amount == Decimal("50.0")


def test_cannot_cancel_executed_or_other_users_order(db_session):
    user1, _ = _setup_user(db_session, "user_one", Decimal("1000.00"))
    user2, _ = _setup_user(db_session, "user_two", Decimal("1000.00"))

    order_svc = OrderService(db_session)
    res = order_svc.create_order(
        user_id=user1.id,
        symbol="BTC",
        order_type="BUY_LIMIT",
        amount=Decimal("0.01"),
        target_price=Decimal("10000.00"),
    )
    order = res.value

    # User 2 tries to cancel User 1's order
    cross_res = order_svc.cancel_order(order.id, user2.id)
    assert cross_res.is_failure
    assert "წვდომა შეზღუდულია" in cross_res.error

    # Cancel once
    assert order_svc.cancel_order(order.id, user1.id).is_success

    # Cancel again
    again_res = order_svc.cancel_order(order.id, user1.id)
    assert again_res.is_failure
    assert "მხოლოდ PENDING" in again_res.error


def test_get_orders_filtering(db_session):
    user, _ = _setup_user(db_session, "user_filter", Decimal("50000.00"))
    order_svc = OrderService(db_session)

    o1 = order_svc.create_order(user.id, "BTC", "BUY_LIMIT", Decimal("0.01"), Decimal("50000")).value
    o2 = order_svc.create_order(user.id, "ETH", "BUY_LIMIT", Decimal("0.1"), Decimal("3000")).value
    order_svc.cancel_order(o1.id, user.id)

    # All
    all_orders = order_svc.get_orders(user.id, "ALL")
    assert len(all_orders) == 2

    # Pending
    pending = order_svc.get_orders(user.id, "PENDING")
    assert len(pending) == 1
    assert pending[0].id == o2.id

    # Cancelled
    cancelled = order_svc.get_orders(user.id, "CANCELLED")
    assert len(cancelled) == 1
    assert cancelled[0].id == o1.id
