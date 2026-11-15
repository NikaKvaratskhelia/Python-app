from decimal import Decimal
from core.database import get_db
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.models.watchlist_model import WatchlistModel
from infrastructure.persistence.models.price_alert_model import PriceAlertModel
from domain.aggregates.user import UserRole
from seed_data import seed_database


def test_seed_database():
    seed_database()

    with get_db() as db:
        # 1. Admin checks
        admin = db.query(UserModel).filter(UserModel.username == "admin").first()
        assert admin is not None
        assert admin.role == UserRole.ADMIN

        admin_wallet = db.query(WalletModel).filter(WalletModel.user_id == admin.id).first()
        assert admin_wallet is not None
        assert admin_wallet.fiat_balance == Decimal("100000.00")

        # 2. Trader checks
        trader = db.query(UserModel).filter(UserModel.username == "trader").first()
        assert trader is not None
        assert trader.role == UserRole.REGULAR

        trader_wallet = db.query(WalletModel).filter(WalletModel.user_id == trader.id).first()
        assert trader_wallet is not None
        assert trader_wallet.fiat_balance == Decimal("25000.00")
        assert len(trader_wallet.assets) == 3

        orders = db.query(OrderModel).filter(OrderModel.wallet_id == trader_wallet.id).all()
        assert len(orders) == 4

        watchlist = db.query(WatchlistModel).filter(WatchlistModel.user_id == trader.id).all()
        assert len(watchlist) == 4

        alerts = db.query(PriceAlertModel).filter(PriceAlertModel.user_id == trader.id).all()
        assert len(alerts) == 2

        # 3. Alice checks
        alice = db.query(UserModel).filter(UserModel.username == "alice").first()
        assert alice is not None
