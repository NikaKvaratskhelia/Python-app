from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.result import Result
from domain.aggregates.user.enums.user_role import UserRole
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.order_model import OrderModel, OrderStatus
from infrastructure.persistence.models.price_alert_model import PriceAlertModel
from services.order_bot_engine import OrderBotEngine


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_users(self) -> List[Dict[str, Any]]:
        users = (
            self.db.query(UserModel)
            .order_by(UserModel.id.asc())
            .all()
        )

        user_list = []
        for user in users:
            wallet = (
                self.db.query(WalletModel)
                .options(joinedload(WalletModel.assets))
                .filter(WalletModel.user_id == user.id)
                .first()
            )

            fiat_balance = wallet.fiat_balance if wallet else Decimal("0.00")
            assets = wallet.assets if wallet else []
            assets_str = ", ".join([f"{a.amount} {a.symbol}" for a in assets if a.amount > 0]) or "არ აქვს"

            orders_count = (
                self.db.query(OrderModel)
                .join(WalletModel, OrderModel.wallet_id == WalletModel.id)
                .filter(WalletModel.user_id == user.id)
                .count()
            )

            role_val = user.role.value if hasattr(user.role, "value") else str(user.role)

            user_list.append({
                "id": user.id,
                "username": user.username,
                "role": role_val,
                "created_at": user.created_at,
                "fiat_balance": fiat_balance,
                "assets_summary": assets_str,
                "orders_count": orders_count,
            })

        return user_list

    def change_user_role(
        self, target_user_id: int, new_role: str, admin_user_id: int
    ) -> Result[None, str]:
        target_user_id = int(target_user_id)
        admin_user_id = int(admin_user_id)

        if target_user_id == admin_user_id:
            return Result.failure("საკუთარ როლს ვერ შეიცვლით.")

        role_clean = new_role.strip().lower()
        if role_clean == "admin":
            role_enum = UserRole.ADMIN
        elif role_clean == "regular":
            role_enum = UserRole.REGULAR
        else:
            return Result.failure("არასწორი როლი. დასაშვებია: ADMIN ან REGULAR.")

        with get_db(self.db) as db:
            user = db.query(UserModel).filter(UserModel.id == target_user_id).first()
            if not user:
                return Result.failure("მომხმარებელი ვერ მოიძებნა.")

            current_role = user.role.value if hasattr(user.role, "value") else str(user.role)
            if current_role == role_enum.value:
                return Result.failure(f"მომხმარებელს უკვე აქვს როლი: {role_enum.value.upper()}.")

            user.role = role_enum

        return Result.success(None)

    def adjust_user_balance(
        self, target_user_id: int, amount: Decimal, admin_user_id: int
    ) -> Result[Decimal, str]:
        target_user_id = int(target_user_id)

        if amount == Decimal("0"):
            return Result.failure("თანხა არ შეიძლება იყოს 0.")

        with get_db(self.db) as db:
            user = db.query(UserModel).filter(UserModel.id == target_user_id).first()
            if not user:
                return Result.failure("მომხმარებელი ვერ მოიძებნა.")

            wallet = db.query(WalletModel).filter(WalletModel.user_id == target_user_id).first()
            if not wallet:
                wallet = WalletModel(user_id=target_user_id, fiat_balance=Decimal("0.00"))
                db.add(wallet)

            new_balance = wallet.fiat_balance + amount
            if new_balance < Decimal("0"):
                return Result.failure(
                    f"არასაკმარისი ბალანსი ჩამოსაჭრელად. ხელმისაწვდომია: ${wallet.fiat_balance:,.2f}."
                )

            wallet.fiat_balance = new_balance

            tx_type = "ADMIN_CREDIT" if amount > 0 else "ADMIN_DEBIT"
            tx = TransactionModel(
                wallet_id=wallet.id,
                type=tx_type,
                amount=abs(amount),
                price=Decimal("1.00"),
                symbol="USD",
            )
            db.add(tx)

        return Result.success(new_balance)

    def get_platform_stats(self) -> Dict[str, Any]:
        total_users = self.db.query(UserModel).count()

        wallets = self.db.query(WalletModel).all()
        total_fiat = sum((w.fiat_balance for w in wallets), Decimal("0.00"))

        total_txs = self.db.query(TransactionModel).count()
        pending_orders = self.db.query(OrderModel).filter(OrderModel.status == OrderStatus.PENDING.value).count()
        executed_orders = self.db.query(OrderModel).filter(OrderModel.status == OrderStatus.EXECUTED.value).count()
        cancelled_orders = self.db.query(OrderModel).filter(OrderModel.status == OrderStatus.CANCELLED.value).count()
        active_alerts = self.db.query(PriceAlertModel).filter(PriceAlertModel.is_triggered == False).count()
        fee_txs = self.db.query(TransactionModel).filter(TransactionModel.type == "FEE").all()
        total_fees = sum((t.amount for t in fee_txs), Decimal("0.00"))

        return {
            "total_users": total_users,
            "total_fiat_liquidity": total_fiat,
            "total_transactions": total_txs,
            "total_fees_collected": total_fees,
            "pending_orders": pending_orders,
            "executed_orders": executed_orders,
            "cancelled_orders": cancelled_orders,
            "active_alerts": active_alerts,
        }

    def get_global_transactions(self, limit: int = 30) -> List[Dict[str, Any]]:
        txs = (
            self.db.query(TransactionModel)
            .options(joinedload(TransactionModel.wallet).joinedload(WalletModel.user))
            .order_by(TransactionModel.id.desc())
            .limit(limit)
            .all()
        )

        result = []
        for tx in txs:
            username = tx.wallet.user.username if (tx.wallet and tx.wallet.user) else "N/A"
            total = tx.amount * tx.price if (tx.amount and tx.price) else Decimal("0.00")
            result.append({
                "id": tx.id,
                "username": username,
                "type": tx.type,
                "symbol": tx.symbol or "USD",
                "amount": tx.amount,
                "price": tx.price,
                "total": total,
                "created_at": tx.created_at,
            })

        return result

    def get_bot_status(self) -> Dict[str, Any]:
        pending_orders = (
            self.db.query(OrderModel)
            .filter(OrderModel.status == OrderStatus.PENDING.value)
            .count()
        )
        active_alerts = (
            self.db.query(PriceAlertModel)
            .filter(PriceAlertModel.is_triggered == False)
            .count()
        )

        return {
            "is_running": OrderBotEngine._running,
            "pending_orders": pending_orders,
            "active_alerts": active_alerts,
        }

    def force_run_bot_cycle(self) -> None:
        OrderBotEngine.check_orders_once(self.db)
