from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.user_model import UserModel


class FeeService:
    DEFAULT_FEE_RATE = Decimal("0.001")  # 0.1% platform trading fee

    @staticmethod
    def calculate_fee(trade_value: Decimal, fee_rate: Decimal = DEFAULT_FEE_RATE) -> Decimal:
        if trade_value <= Decimal("0"):
            return Decimal("0.00")
        raw_fee = trade_value * fee_rate
        # Minimum fee is $0.01
        rounded = raw_fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return max(rounded, Decimal("0.01"))

    @staticmethod
    def record_fee(
        db: Session,
        wallet_id: int,
        fee_amount: Decimal,
        trade_type: str,
        symbol: str,
    ) -> TransactionModel:
        tx = TransactionModel(
            wallet_id=wallet_id,
            type="FEE",
            symbol="USD",
            amount=fee_amount,
            price=Decimal("1.00"),
        )
        with get_db(db) as session:
            session.add(tx)
        return tx

    @staticmethod
    def get_total_platform_revenue(db: Session) -> Decimal:
        fee_txs = (
            db.query(TransactionModel)
            .filter(TransactionModel.type == "FEE")
            .all()
        )
        return sum((tx.amount for tx in fee_txs), Decimal("0.00"))

    @staticmethod
    def get_fee_history(db: Session, limit: int = 30) -> List[Dict[str, Any]]:
        fee_txs = (
            db.query(TransactionModel)
            .options(joinedload(TransactionModel.wallet).joinedload(WalletModel.user))
            .filter(TransactionModel.type == "FEE")
            .order_by(TransactionModel.id.desc())
            .limit(limit)
            .all()
        )

        history = []
        for tx in fee_txs:
            username = tx.wallet.user.username if (tx.wallet and tx.wallet.user) else "N/A"
            history.append({
                "id": tx.id,
                "username": username,
                "amount": tx.amount,
                "created_at": tx.created_at,
            })
        return history
