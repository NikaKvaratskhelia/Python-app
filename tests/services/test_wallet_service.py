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


def test_wallet_service_withdraw(db_session):
    user_id = _create_test_user(db_session, "user_wd")
    service = WalletService(db_session)

    # Initial balance is 10,000
    res = service.withdraw(user_id, Decimal("3000.00"))
    assert res.is_success
    assert res.value.fiat_balance == Decimal("7000.00")

    # Exceeding balance
    bad_res = service.withdraw(user_id, Decimal("8000.00"))
    assert bad_res.is_failure
    assert "არასაკმარისი ბალანსი" in bad_res.error


def test_wallet_service_transfer_usd(db_session):
    sender_id = _create_test_user(db_session, "sender_u")
    receiver_id = _create_test_user(db_session, "receiver_u")
    service = WalletService(db_session)

    # Transfer 2000 USD
    res = service.transfer(sender_id, "receiver_u", "USD", Decimal("2000.00"))
    assert res.is_success

    sender_w = service.get_or_create_wallet(sender_id)
    receiver_w = service.get_or_create_wallet(receiver_id)

    assert sender_w.fiat_balance == Decimal("8000.00")
    assert receiver_w.fiat_balance == Decimal("12000.00")


def test_wallet_service_transfer_crypto(db_session):
    sender_id = _create_test_user(db_session, "sender_crypto")
    receiver_id = _create_test_user(db_session, "receiver_crypto")
    service = WalletService(db_session)

    # Sender buys 2 SOL
    service.buy_asset(sender_id, "SOL", Decimal("2.0"), Decimal("150.00"))

    # Transfer 1.5 SOL to receiver
    res = service.transfer(sender_id, "receiver_crypto", "SOL", Decimal("1.5"))
    assert res.is_success

    sender_w = service.get_or_create_wallet(sender_id)
    receiver_w = service.get_or_create_wallet(receiver_id)

    sender_sol = next(a for a in sender_w.assets if a.symbol == "SOL")
    receiver_sol = next(a for a in receiver_w.assets if a.symbol == "SOL")

    assert sender_sol.amount == Decimal("0.5")
    assert receiver_sol.amount == Decimal("1.5")


def test_wallet_service_transfer_validation(db_session):
    sender_id = _create_test_user(db_session, "sender_val")
    receiver_id = _create_test_user(db_session, "receiver_val")
    service = WalletService(db_session)

    # Transfer with alternative kwargs (from_user_id, to_username, symbol)
    kwarg_res = service.transfer(
        from_user_id=sender_id,
        to_username="receiver_val",
        symbol="USD",
        amount=Decimal("50.00"),
    )
    assert kwarg_res.is_success

    # Transfer to self
    self_res = service.transfer(sender_id, "sender_val", "USD", Decimal("100.00"))
    assert self_res.is_failure
    assert "დაუშვებელია" in self_res.error

    # Non-existent receiver
    none_res = service.transfer(sender_id, "ghost_user", "USD", Decimal("100.00"))
    assert none_res.is_failure
    assert "ვერ მოიძებნა" in none_res.error


def test_wallet_service_export_csv(db_session, tmp_path):
    user_id = _create_test_user(db_session, "csv_user")
    service = WalletService(db_session)
    service.deposit(user_id, Decimal("500.00"))

    export_res = service.export_transactions_csv(user_id, directory=str(tmp_path))
    assert export_res.is_success
    import os
    assert os.path.exists(export_res.value)


def test_wallet_service_advanced_analytics(db_session, monkeypatch):
    user_id = _create_test_user(db_session, "analytics_user")
    service = WalletService(db_session)
    service.buy_asset(user_id, "ETH", Decimal("1.0"), Decimal("2000.00"))

    monkeypatch.setattr(
        MarketService,
        "get_all_active_prices",
        lambda: {"ETH": {"price": Decimal("2500.00"), "change": Decimal("10.0")}},
    )

    analytics = service.get_advanced_portfolio_analytics(user_id)
    assert len(analytics["allocations"]) == 2  # USD + ETH
    assert analytics["unrealized_pnl"] == Decimal("500.00")
