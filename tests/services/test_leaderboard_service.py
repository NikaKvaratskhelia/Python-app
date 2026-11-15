from decimal import Decimal
from domain.aggregates.user.enums.user_role import UserRole
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.security.security import hash_password
from services.leaderboard_service import LeaderboardService


def test_leaderboard_ranking(db_session, monkeypatch):
    # User 1: Rich ($10,000)
    u1 = UserModel(username="rich_trader", password_hash=hash_password("Pass1!"), role=UserRole.REGULAR)
    # User 2: Medium ($5,000)
    u2 = UserModel(username="med_trader", password_hash=hash_password("Pass2!"), role=UserRole.REGULAR)
    # User 3: Poor ($1,000)
    u3 = UserModel(username="poor_trader", password_hash=hash_password("Pass3!"), role=UserRole.REGULAR)

    db_session.add_all([u1, u2, u3])
    db_session.commit()

    w1 = WalletModel(user_id=u1.id, fiat_balance=Decimal("10000.00"))
    w2 = WalletModel(user_id=u2.id, fiat_balance=Decimal("5000.00"))
    w3 = WalletModel(user_id=u3.id, fiat_balance=Decimal("1000.00"))
    db_session.add_all([w1, w2, w3])
    db_session.commit()

    board = LeaderboardService.get_leaderboard(db_session, limit=10)
    assert len(board) >= 3

    # First ranked must be rich_trader
    assert board[0]["username"] == "rich_trader"
    assert board[0]["rank"] == 1
    assert board[0]["net_worth"] == Decimal("10000.00")

    # Second ranked must be med_trader
    assert board[1]["username"] == "med_trader"
    assert board[1]["rank"] == 2

    # Third ranked must be poor_trader
    assert board[2]["username"] == "poor_trader"
    assert board[2]["rank"] == 3


def test_leaderboard_trade_stats(db_session):
    u = UserModel(username="active_trader", password_hash=hash_password("Pass!"), role=UserRole.REGULAR)
    db_session.add(u)
    db_session.commit()

    w = WalletModel(user_id=u.id, fiat_balance=Decimal("2000.00"))
    db_session.add(w)
    db_session.commit()

    tx1 = TransactionModel(wallet_id=w.id, type="BUY", symbol="BTC", amount=Decimal("0.1"), price=Decimal("10000.00"))
    tx2 = TransactionModel(wallet_id=w.id, type="SELL", symbol="BTC", amount=Decimal("0.05"), price=Decimal("12000.00"))
    db_session.add_all([tx1, tx2])
    db_session.commit()

    board = LeaderboardService.get_leaderboard(db_session, limit=5)
    trader = next(t for t in board if t["username"] == "active_trader")
    assert trader["trades_count"] == 2
    # 0.1 * 10000 = 1000 + 0.05 * 12000 = 600 -> volume 1600
    assert trader["trading_volume"] == Decimal("1600.00")
