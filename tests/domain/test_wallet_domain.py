from decimal import Decimal
from domain.aggregates.wallet.entities.wallet import Wallet
from domain.aggregates.wallet.entities.wallet_asset import WalletAsset


def test_wallet_asset_update_on_buy():
    asset = WalletAsset(
        symbol="BTC", amount=Decimal("1.0"), average_buy_price=Decimal("50000.00")
    )

    # Buy additional 1.0 BTC at $60,000.00 -> New average should be $55,000.00
    res = asset.update_on_buy(Decimal("1.0"), Decimal("60000.00"))
    assert res.is_success is True
    assert asset.amount == Decimal("2.0")
    assert asset.average_buy_price == Decimal("55000.00")

    # Buy invalid amount (<= 0)
    bad_buy = asset.update_on_buy(Decimal("0"), Decimal("50000.00"))
    assert bad_buy.is_failure is True
    assert "რაოდენობა უნდა იყოს 0-ზე მეტი." in bad_buy.error


def test_wallet_asset_update_on_sell():
    asset = WalletAsset(
        symbol="ETH", amount=Decimal("2.5"), average_buy_price=Decimal("3000.00")
    )

    # Sell 1.0 ETH
    res = asset.update_on_sell(Decimal("1.0"))
    assert res.is_success is True
    assert asset.amount == Decimal("1.5")
    # Average buy price does not change on selling
    assert asset.average_buy_price == Decimal("3000.00")

    # Sell invalid (<= 0)
    bad_zero = asset.update_on_sell(Decimal("-0.5"))
    assert bad_zero.is_failure is True

    # Sell more than owned
    bad_excess = asset.update_on_sell(Decimal("2.0"))
    assert bad_excess.is_failure is True
    assert "აღემატება ფლობილს" in bad_excess.error
    assert asset.amount == Decimal("1.5")


def test_wallet_deposit():
    wallet = Wallet(id=1, user_id=1, fiat_balance=Decimal("1000.00"))

    # Successful deposit
    ok = wallet.deposit(Decimal("500.00"))
    assert ok.is_success is True
    assert wallet.fiat_balance == Decimal("1500.00")

    # Invalid deposit (zero or negative)
    bad_zero = wallet.deposit(Decimal("0.00"))
    assert bad_zero.is_failure is True
    assert "0-ზე მეტი" in bad_zero.error

    bad_neg = wallet.deposit(Decimal("-10.00"))
    assert bad_neg.is_failure is True
    assert wallet.fiat_balance == Decimal("1500.00")


def test_wallet_withdraw():
    wallet = Wallet(id=1, user_id=1, fiat_balance=Decimal("500.00"))

    # Successful withdraw
    ok = wallet.withdraw(Decimal("200.00"))
    assert ok.is_success is True
    assert wallet.fiat_balance == Decimal("300.00")

    # Invalid withdraw (zero or negative)
    bad_zero = wallet.withdraw(Decimal("0.00"))
    assert bad_zero.is_failure is True

    # Insufficient funds
    bad_funds = wallet.withdraw(Decimal("400.00"))
    assert bad_funds.is_failure is True
    assert "არასაკმარისი ბალანსი" in bad_funds.error
    assert wallet.fiat_balance == Decimal("300.00")


def test_wallet_buy_asset():
    wallet = Wallet(id=1, user_id=1, fiat_balance=Decimal("10000.00"))

    # Buy 0.1 BTC at $50,000 -> Total cost $5,000
    res = wallet.buy_asset("BTC", Decimal("0.1"), Decimal("50000.00"))
    assert res.is_success is True
    assert wallet.fiat_balance == Decimal("5000.00")
    assert len(wallet.assets) == 1
    assert wallet.assets[0].symbol == "BTC"
    assert wallet.assets[0].amount == Decimal("0.1")
    assert wallet.assets[0].average_buy_price == Decimal("50000.00")

    # Buy more BTC at $60,000 -> 0.05 BTC costing $3,000
    res2 = wallet.buy_asset("BTC", Decimal("0.05"), Decimal("60000.00"))
    assert res2.is_success is True
    assert wallet.fiat_balance == Decimal("2000.00")
    assert len(wallet.assets) == 1
    assert wallet.assets[0].amount == Decimal("0.15")

    # Insufficient balance to buy
    res3 = wallet.buy_asset("BTC", Decimal("0.1"), Decimal("50000.00"))
    assert res3.is_failure is True
    assert "არასაკმარისი ბალანსი" in res3.error
    assert wallet.fiat_balance == Decimal("2000.00")

    # Invalid amount or price
    bad_amount = wallet.buy_asset("ETH", Decimal("-1"), Decimal("3000.00"))
    assert bad_amount.is_failure is True


def test_wallet_sell_asset():
    wallet = Wallet(id=1, user_id=1, fiat_balance=Decimal("1000.00"))
    wallet.buy_asset("SOL", Decimal("10"), Decimal("100.00"))
    assert wallet.fiat_balance == Decimal("0.00")

    # Sell 4 SOL at $120 -> $480 added
    sell_ok = wallet.sell_asset("SOL", Decimal("4"), Decimal("120.00"))
    assert sell_ok.is_success is True
    assert wallet.fiat_balance == Decimal("480.00")
    assert wallet.assets[0].amount == Decimal("6")

    # Try selling non-existent asset
    sell_none = wallet.sell_asset("DOGE", Decimal("100"), Decimal("0.10"))
    assert sell_none.is_failure is True
    assert "არ არის საკმარისი DOGE" in sell_none.error

    # Try selling more than owned
    sell_excess = wallet.sell_asset("SOL", Decimal("10"), Decimal("120.00"))
    assert sell_excess.is_failure is True
    assert "არ არის საკმარისი SOL" in sell_excess.error
