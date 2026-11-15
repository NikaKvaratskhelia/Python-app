"""
Database Seeder Script.
Cleans all tables and seeds fresh demo data for project presentation and testing.
Includes 1 Admin user, 1 Primary Trader with portfolio & active orders, and 1 P2P Counterparty.
All database transactions are managed automatically by the get_db context manager.
"""

from decimal import Decimal
from sqlalchemy import text
from core.database import get_db
import infrastructure.persistence.models  # ensure all models registered
from domain.aggregates.user import UserRole
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.order_model import OrderModel, OrderType, OrderStatus
from infrastructure.persistence.models.watchlist_model import WatchlistModel
from infrastructure.persistence.models.price_alert_model import PriceAlertModel
from infrastructure.security.security import hash_password


def clean_database(db):
    """Truncates all project tables and resets identity counters."""
    print("მიმდინარეობს ბაზის გასუფთავება...")
    truncate_sql = text("""
        TRUNCATE TABLE 
            price_alerts,
            watchlists,
            orders,
            transactions,
            wallet_assets,
            wallets,
            users
        RESTART IDENTITY CASCADE;
    """)
    db.execute(truncate_sql)
    print("ბაზა წარმატებით გასუფთავდა.")


def seed_database():
    with get_db() as db:
        clean_database(db)

        print("\nმიმდინარეობს სატესტო მონაცემების გენერირება...")

        # 1. Admin User & Wallet
        admin_user = UserModel(
            username="admin",
            password_hash=hash_password("Admin123!"),
            role=UserRole.ADMIN,
        )
        admin_wallet = WalletModel(
            user=admin_user,
            fiat_balance=Decimal("100000.00"),
        )
        db.add(admin_user)
        db.add(admin_wallet)

        # 2. Primary Trader User & Wallet
        trader_user = UserModel(
            username="trader",
            password_hash=hash_password("Trader123!"),
            role=UserRole.REGULAR,
        )
        trader_wallet = WalletModel(
            user=trader_user,
            fiat_balance=Decimal("25000.00"),
        )
        db.add(trader_user)
        db.add(trader_wallet)

        # Crypto Assets for Trader
        assets = [
            WalletAssetModel(
                wallet=trader_wallet,
                symbol="BTC",
                amount=Decimal("0.50000000"),
                average_buy_price=Decimal("62500.00"),
            ),
            WalletAssetModel(
                wallet=trader_wallet,
                symbol="ETH",
                amount=Decimal("4.00000000"),
                average_buy_price=Decimal("1750.00"),
            ),
            WalletAssetModel(
                wallet=trader_wallet,
                symbol="SOL",
                amount=Decimal("25.00000000"),
                average_buy_price=Decimal("135.00"),
            ),
        ]
        db.add_all(assets)

        # Transactions for Trader
        txs = [
            TransactionModel(
                wallet=trader_wallet,
                type="DEPOSIT",
                symbol="USD",
                amount=Decimal("50000.00"),
                price=Decimal("1.00"),
            ),
            TransactionModel(
                wallet=trader_wallet,
                type="BUY",
                symbol="BTC",
                amount=Decimal("0.50000000"),
                price=Decimal("62500.00"),
            ),
            TransactionModel(
                wallet=trader_wallet,
                type="BUY",
                symbol="ETH",
                amount=Decimal("4.00000000"),
                price=Decimal("1750.00"),
            ),
            TransactionModel(
                wallet=trader_wallet,
                type="BUY",
                symbol="SOL",
                amount=Decimal("25.00000000"),
                price=Decimal("135.00"),
            ),
        ]
        db.add_all(txs)

        # Orders for Trader
        orders = [
            OrderModel(
                wallet=trader_wallet,
                symbol="BTC",
                order_type=OrderType.BUY_LIMIT.value,
                target_price=Decimal("58000.00"),
                amount=Decimal("0.10000000"),
                status=OrderStatus.PENDING.value,
                is_reserved=True,
            ),
            OrderModel(
                wallet=trader_wallet,
                symbol="ETH",
                order_type=OrderType.SELL_LIMIT.value,
                target_price=Decimal("2500.00"),
                amount=Decimal("1.00000000"),
                status=OrderStatus.PENDING.value,
                is_reserved=True,
            ),
            OrderModel(
                wallet=trader_wallet,
                symbol="BTC",
                order_type=OrderType.STOP_LOSS.value,
                target_price=Decimal("55000.00"),
                amount=Decimal("0.10000000"),
                status=OrderStatus.PENDING.value,
                is_reserved=True,
            ),
            OrderModel(
                wallet=trader_wallet,
                symbol="ETH",
                order_type=OrderType.BUY_LIMIT.value,
                target_price=Decimal("1750.00"),
                amount=Decimal("1.00000000"),
                status=OrderStatus.EXECUTED.value,
                is_reserved=False,
            ),
        ]
        db.add_all(orders)

        # Watchlist for Trader
        watchlist_items = [
            WatchlistModel(user=trader_user, symbol="BTC"),
            WatchlistModel(user=trader_user, symbol="ETH"),
            WatchlistModel(user=trader_user, symbol="SOL"),
            WatchlistModel(user=trader_user, symbol="BNB"),
        ]
        db.add_all(watchlist_items)

        # Price Alerts for Trader
        alerts = [
            PriceAlertModel(
                user=trader_user,
                symbol="BTC",
                target_price=Decimal("70000.00"),
                condition="ABOVE",
                is_triggered=False,
            ),
            PriceAlertModel(
                user=trader_user,
                symbol="ETH",
                target_price=Decimal("1500.00"),
                condition="BELOW",
                is_triggered=False,
            ),
        ]
        db.add_all(alerts)

        # 3. Second User (Alice) for testing P2P internal transfer
        alice_user = UserModel(
            username="alice",
            password_hash=hash_password("Alice123!"),
            role=UserRole.REGULAR,
        )
        alice_wallet = WalletModel(
            user=alice_user,
            fiat_balance=Decimal("5000.00"),
        )
        alice_asset = WalletAssetModel(
            wallet=alice_wallet,
            symbol="BTC",
            amount=Decimal("0.10000000"),
            average_buy_price=Decimal("63000.00"),
        )
        db.add(alice_user)
        db.add(alice_wallet)
        db.add(alice_asset)

        # No db.flush() or db.commit() needed here!
        # get_db context manager automatically commits on block exit.

    print("\nსატესტო მონაცემები წარმატებით შეიქმნა!\n")
    print("=" * 60)
    print("მომხმარებლების ანგარიშები ტესტირებისთვის:")
    print("=" * 60)
    print("1. ადმინისტრატორი (Admin):")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("   როლი:     ADMIN")
    print("   ბალანსი:  $100,000.00 USD\n")
    print("2. მთავარი მომხმარებელი (Trader):")
    print("   Username: trader")
    print("   Password: Trader123!")
    print("   როლი:     REGULAR")
    print("   ბალანსი:  $25,000.00 USD")
    print("   აქტივები: 0.5 BTC, 4.0 ETH, 25.0 SOL")
    print("   ორდერები: 3 PENDING (BUY_LIMIT, SELL_LIMIT, STOP_LOSS)")
    print("   Watchlist: BTC, ETH, SOL, BNB")
    print("   Alerts:   BTC > $70k, ETH < $1.5k\n")
    print("3. მეორე მომხმარებელი (P2P ტრანსფერების სატესტოდ):")
    print("   Username: alice")
    print("   Password: Alice123!")
    print("   როლი:     REGULAR")
    print("   ბალანსი:  $5,000.00 USD, 0.1 BTC")
    print("=" * 60)


if __name__ == "__main__":
    seed_database()
