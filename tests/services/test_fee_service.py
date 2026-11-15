from decimal import Decimal
import pytest
from core.database import get_db
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.security.security import hash_password
from domain.aggregates.user.enums.user_role import UserRole
from services.fee_service import FeeService
from services.wallet_service import WalletService


def _setup_user(db_session, username="fee_trader", fiat="1000.00"):
    user = UserModel(
        username=username,
        password_hash=hash_password("Pass123!"),
        role=UserRole.REGULAR,
    )
    db_session.add(user)
    db_session.commit()

    wallet = WalletModel(user_id=user.id, fiat_balance=Decimal(fiat))
    db_session.add(wallet)
    db_session.commit()
    return user, wallet


def test_calculate_fee():
    # 0.1% of $1,000 is $1.00
    fee = FeeService.calculate_fee(Decimal("1000.00"))
    assert fee == Decimal("1.00")

    # 0.1% of $50,000 is $50.00
    fee_btc = FeeService.calculate_fee(Decimal("50000.00"))
    assert fee_btc == Decimal("50.00")

    # Minimum fee is $0.01
    tiny_fee = FeeService.calculate_fee(Decimal("1.00"))
    assert tiny_fee == Decimal("0.01")

    # Zero value has zero fee
    assert FeeService.calculate_fee(Decimal("0.00")) == Decimal("0.00")


def test_record_fee_and_get_platform_revenue(db_session):
    user, wallet = _setup_user(db_session, "fee_user1")

    fee1 = FeeService.calculate_fee(Decimal("2000.00"))  # $2.00
    fee2 = FeeService.calculate_fee(Decimal("5000.00"))  # $5.00

    FeeService.record_fee(db_session, wallet.id, fee1, "BUY", "BTC")
    FeeService.record_fee(db_session, wallet.id, fee2, "SELL", "ETH")

    revenue = FeeService.get_total_platform_revenue(db_session)
    assert revenue == Decimal("7.00")

    history = FeeService.get_fee_history(db_session)
    assert len(history) == 2
    assert history[0]["amount"] == Decimal("5.00")
    assert history[1]["amount"] == Decimal("2.00")


def test_wallet_buy_with_fee(db_session):
    user, wallet = _setup_user(db_session, "fee_buyer", "1000.00")
    service = WalletService(db_session)

    # Buy $500 worth of SOL, with $0.50 fee
    trade_val = Decimal("500.00")
    fee = FeeService.calculate_fee(trade_val)
    assert fee == Decimal("0.50")

    res = service.buy_asset(user.id, "SOL", Decimal("5.0"), Decimal("100.00"), fee=fee)
    assert res.is_success
    saved_wallet = res.value

    # 1000 - 500 - 0.50 = 499.50
    assert saved_wallet.fiat_balance == Decimal("499.50")

    # Check fee transaction was created
    txs = db_session.query(TransactionModel).filter(TransactionModel.wallet_id == wallet.id).all()
    types = [t.type for t in txs]
    assert "BUY" in types
    assert "FEE" in types


def test_wallet_sell_with_fee(db_session):
    user, wallet = _setup_user(db_session, "fee_seller", "1000.00")
    service = WalletService(db_session)

    # Buy 2 ETH first without fee
    service.buy_asset(user.id, "ETH", Decimal("2.0"), Decimal("200.00"))
    db_session.commit()

    # Sell 1 ETH at $300 ($300 gross, 0.1% fee = $0.30 -> net $299.70)
    fee = FeeService.calculate_fee(Decimal("300.00"))
    assert fee == Decimal("0.30")

    res = service.sell_asset(user.id, "ETH", Decimal("1.0"), Decimal("300.00"), fee=fee)
    assert res.is_success
    saved_wallet = res.value

    # Started with 1000, spent 400 = 600. Sold for 300 - 0.30 = 299.70 -> 899.70
    assert saved_wallet.fiat_balance == Decimal("899.70")
