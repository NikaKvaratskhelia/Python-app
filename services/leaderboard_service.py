from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from services.binance_ws import BinanceWSManager


class LeaderboardService:
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        users = (
            db.query(UserModel)
            .order_by(UserModel.id.asc())
            .all()
        )

        market_prices = BinanceWSManager.get_all_prices()

        leaderboard_data = []

        for user in users:
            wallet = (
                db.query(WalletModel)
                .options(joinedload(WalletModel.assets))
                .filter(WalletModel.user_id == user.id)
                .first()
            )

            fiat_balance = wallet.fiat_balance if wallet else Decimal("0.00")
            crypto_value = Decimal("0.00")
            top_asset_str = "არ აქვს"
            max_asset_val = Decimal("0.00")

            if wallet and wallet.assets:
                for asset in wallet.assets:
                    if asset.amount <= Decimal("0"):
                        continue

                    price_info = market_prices.get(asset.symbol)
                    unit_price = price_info["price"] if price_info else Decimal("0.00")
                    asset_val = asset.amount * unit_price
                    crypto_value += asset_val

                    if asset_val > max_asset_val:
                        max_asset_val = asset_val
                        top_asset_str = f"{asset.amount} {asset.symbol}"

            net_worth = fiat_balance + crypto_value

            # Trade statistics
            trade_txs = (
                db.query(TransactionModel)
                .join(WalletModel, TransactionModel.wallet_id == WalletModel.id)
                .filter(
                    WalletModel.user_id == user.id,
                    TransactionModel.type.in_(["BUY", "SELL"]),
                )
                .all()
            )

            trades_count = len(trade_txs)
            trading_volume = sum(
                ((tx.amount * tx.price) for tx in trade_txs if tx.amount and tx.price),
                Decimal("0.00"),
            )

            role_str = (
                user.role.value if hasattr(user.role, "value") else str(user.role)
            )

            leaderboard_data.append({
                "user_id": user.id,
                "username": user.username,
                "role": role_str,
                "net_worth": net_worth,
                "fiat_balance": fiat_balance,
                "crypto_value": crypto_value,
                "trades_count": trades_count,
                "trading_volume": trading_volume,
                "top_asset": top_asset_str,
            })

        # Sort by Net Worth descending
        leaderboard_data.sort(key=lambda x: x["net_worth"], reverse=True)

        # Assign ranks
        ranked = []
        for rank, entry in enumerate(leaderboard_data[:limit], start=1):
            entry["rank"] = rank
            ranked.append(entry)

        return ranked
