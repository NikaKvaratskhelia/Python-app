from decimal import Decimal
from domain.aggregates.user.entities.user import User
from infrastructure.persistence.repositories.user_repository import UserRepository
from services.wallet_service import WalletService
from services.market_service import MarketService


def _create_test_user(db_session, username="wallet_svc_user") -> int:
    repo = UserRepository(db_session)
    user = User(username=username, password_hash="hash")
    repo.save(user)
    db_session.commit()
    saved = repo.get_by_username(username)
    return saved.id


def test_wallet_service_get_or_create(db_session):
    user_id = _create_test_user(db_session, "user1")
    service = WalletService(db_session)

    wallet = service.get_or_create_wallet(user_id)
    assert wallet is not None
    assert wallet.user_id == user_id
    assert wallet.fiat_balance == Decimal("10000.00")

    # Second call returns the existing wallet
    same_wallet = service.get_or_create_wallet(user_id)
    assert same_wallet.id == wallet.id


def test_wallet_service_deposit(db_session):
    user_id = _create_test_user(db_session, "user2")
    service = WalletService(db_session)

    res = service.deposit(user_id, Decimal("500.00"))
    db_session.commit()

    assert res.is_success is True
    assert res.value.fiat_balance == Decimal("10500.00")

    # Negative deposit fails as bad result
    bad_res = service.deposit(user_id, Decimal("-100.00"))
    assert bad_res.is_failure is True
    assert "0-ზე მეტი" in bad_res.error


def test_wallet_service_buy_and_sell_asset(db_session):
    user_id = _create_test_user(db_session, "user3")
    service = WalletService(db_session)

    # Buy 0.1 BTC at $50,000 -> Cost $5,000 -> Remaining balance $5,000
    buy_res = service.buy_asset(user_id, "BTC", Decimal("0.1"), Decimal("50000.00"))
    db_session.commit()

    assert buy_res.is_success is True
    wallet = buy_res.value
    assert wallet.fiat_balance == Decimal("5000.00")
    assert len(wallet.assets) == 1
    assert wallet.assets[0].symbol == "BTC"
    assert wallet.assets[0].amount == Decimal("0.1")

    # Buy exceeding fiat balance fails as bad result
    fail_buy = service.buy_asset(user_id, "BTC", Decimal("1.0"), Decimal("50000.00"))
    assert fail_buy.is_failure is True
    assert "არასაკმარისი ბალანსი" in fail_buy.error

    # Sell 0.05 BTC at $60,000 -> Proceeds $3,000 -> Balance $8,000
    sell_res = service.sell_asset(user_id, "BTC", Decimal("0.05"), Decimal("60000.00"))
    db_session.commit()

    assert sell_res.is_success is True
    assert sell_res.value.fiat_balance == Decimal("8000.00")
    assert sell_res.value.assets[0].amount == Decimal("0.05")

    # Sell more than owned fails as bad result
    fail_sell = service.sell_asset(user_id, "BTC", Decimal("1.0"), Decimal("60000.00"))
    assert fail_sell.is_failure is True
    assert "არ არის საკმარისი BTC" in fail_sell.error


def test_wallet_service_portfolio_summary(db_session, monkeypatch):
    user_id = _create_test_user(db_session, "user4")
    service = WalletService(db_session)

    # Buy 1 ETH at $3,000 -> Fiat remaining: $7,000
    service.buy_asset(user_id, "ETH", Decimal("1.0"), Decimal("3000.00"))
    db_session.commit()

    # Mock market prices
    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {
            "ETH": {
                "price": Decimal("3500.00"),
                "price_change_percent": Decimal("16.67"),
            }
        },
    )

    summary = service.get_portfolio_summary(user_id)
    assert summary["fiat_balance"] == Decimal("7000.00")
    assert summary["total_crypto_value"] == Decimal("3500.00")
    assert summary["total_portfolio_value"] == Decimal("10500.00")
    assert len(summary["assets"]) == 1
    assert summary["assets"][0]["symbol"] == "ETH"
    assert summary["assets"][0]["pnl_usd"] == Decimal("500.00")
