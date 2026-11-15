from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from core.result import Result
from domain.aggregates.user.validators.user_validators import UserValidator
from infrastructure.persistence.models.user_model import UserModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.order_model import OrderModel
from infrastructure.persistence.repositories.user_repository import UserRepository
from infrastructure.security.security import hash_password, verify_password


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_profile(self, user_id: int) -> Result[dict, str]:
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user_model:
            return Result.failure("მომხმარებელი ვერ მოიძებნა.")

        role_str = (
            user_model.role.value
            if hasattr(user_model.role, "value")
            else str(user_model.role)
        )

        return Result.success(
            {
                "id": user_model.id,
                "username": user_model.username,
                "role": role_str,
                "created_at": user_model.created_at,
            }
        )

    def get_account_stats(self, user_id: int) -> Result[dict, str]:
        wallet = (
            self.db.query(WalletModel).filter(WalletModel.user_id == user_id).first()
        )

        if not wallet:
            return Result.failure("საფულე ვერ მოიძებნა.")

        transactions = wallet.transactions or []
        total_tx = len(transactions)

        deposits = [tx for tx in transactions if tx.type == "DEPOSIT"]
        total_deposited = (
            sum(Decimal(str(tx.amount)) for tx in deposits)
            if deposits
            else Decimal("0.00")
        )

        trades_count = sum(
            1 for tx in transactions if tx.type in ("BUY", "SELL", "STOP_LOSS")
        )

        active_orders_count = (
            self.db.query(OrderModel)
            .filter(OrderModel.wallet_id == wallet.id, OrderModel.status == "PENDING")
            .count()
        )

        holding_assets_count = sum(
            1 for asset in wallet.assets if asset.amount > Decimal("0")
        )

        return Result.success(
            {
                "fiat_balance": wallet.fiat_balance,
                "total_transactions": total_tx,
                "total_deposited": total_deposited,
                "trades_count": trades_count,
                "active_orders": active_orders_count,
                "holding_assets_count": holding_assets_count,
            }
        )

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> Result[None, str]:
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user_model:
            return Result.failure("მომხმარებელი ვერ მოიძებნა.")

        if not verify_password(current_password, user_model.password_hash):
            return Result.failure("მიმდინარე პაროლი არასწორია.")

        if current_password == new_password:
            return Result.failure("ახალი პაროლი არ შეიძლება ემთხვეოდეს ძველ პაროლს.")

        val_res = UserValidator.validate_password(new_password)

        if val_res.is_failure:
            return Result.failure(val_res.error)

        user_model.password_hash = hash_password(new_password)
        self.db.flush()

        return Result.success(None)

    def change_username(self, user_id: int, new_username: str) -> Result[str, str]:
        new_username = new_username.strip()
        val_res = UserValidator.validate_username(new_username)

        if val_res.is_failure:
            return Result.failure(val_res.error)

        existing = (
            self.db.query(UserModel).filter(UserModel.username == new_username).first()
        )

        if existing and existing.id != user_id:
            return Result.failure(
                f"მომხმარებელი სახელით '{new_username}' უკვე არსებობს."
            )

        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user_model:
            return Result.failure("მომხმარებელი ვერ მოიძებნა.")

        user_model.username = new_username
        self.db.flush()

        return Result.success(new_username)
