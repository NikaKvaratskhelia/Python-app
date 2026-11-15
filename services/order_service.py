from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from core.result import Result
from infrastructure.persistence.models.order_model import (
    OrderModel,
    OrderType,
    OrderStatus,
)
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from services.wallet_service import WalletService


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.wallet_service = WalletService(db)

    def create_order(
        self,
        user_id: int,
        symbol: str,
        order_type: str,
        amount: Decimal,
        target_price: Decimal,
    ) -> Result[OrderModel, str]:
        symbol = symbol.strip().upper()

        if amount <= Decimal("0"):
            return Result.failure("რაოდენობა უნდა იყოს 0-ზე მეტი.")

        if target_price <= Decimal("0"):
            return Result.failure("სამიზნე ფასი უნდა იყოს 0-ზე მეტი.")

        valid_types = {t.value for t in OrderType}
        if order_type not in valid_types:
            return Result.failure(f"არასწორი ორდერის ტიპი: {order_type}.")

        wallet = (
            self.db.query(WalletModel)
            .options(joinedload(WalletModel.assets))
            .filter(WalletModel.user_id == user_id)
            .first()
        )
        if not wallet:
            self.wallet_service.get_or_create_wallet(user_id)
            wallet = (
                self.db.query(WalletModel)
                .options(joinedload(WalletModel.assets))
                .filter(WalletModel.user_id == user_id)
                .first()
            )

        # 1. BUY_LIMIT: Reserve fiat (amount * target_price)
        if order_type == OrderType.BUY_LIMIT.value:
            required_fiat = amount * target_price
            if wallet.fiat_balance < required_fiat:
                return Result.failure(
                    f"არასაკმარისი ბალანსი. საჭიროა ${required_fiat:,.2f}, ხელმისაწვდომია ${wallet.fiat_balance:,.2f}."
                )
            wallet.fiat_balance -= required_fiat

        # 2. SELL_LIMIT, STOP_LOSS, TAKE_PROFIT: Reserve crypto asset
        elif order_type in (
            OrderType.SELL_LIMIT.value,
            OrderType.STOP_LOSS.value,
            OrderType.TAKE_PROFIT.value,
        ):
            asset = next((a for a in wallet.assets if a.symbol == symbol), None)
            available_amount = asset.amount if asset else Decimal("0")

            if not asset or available_amount < amount:
                return Result.failure(
                    f"არასაკმარისი {symbol} აქტივი. ხელმისაწვდომია: {available_amount}, საჭიროა: {amount}."
                )

            asset.amount -= amount

        order = OrderModel(
            wallet_id=wallet.id,
            symbol=symbol,
            order_type=order_type,
            target_price=target_price,
            amount=amount,
            status=OrderStatus.PENDING.value,
            is_reserved=True,
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return Result.success(order)

    def cancel_order(self, order_id: int, user_id: int) -> Result[OrderModel, str]:
        order = (
            self.db.query(OrderModel)
            .options(joinedload(OrderModel.wallet).joinedload(WalletModel.assets))
            .filter(OrderModel.id == order_id)
            .first()
        )

        if not order:
            return Result.failure(f"ორდერი #{order_id} ვერ მოიძებნა.")

        if order.wallet.user_id != user_id:
            return Result.failure("წვდომა შეზღუდულია: ორდერი თქვენ არ გეკუთვნით.")

        if order.status != OrderStatus.PENDING.value:
            return Result.failure(
                f"შეუძლებელია ორდერის გაუქმება. მხოლოდ PENDING ორდერების გაუქმებაა შესაძლებელი (მიმდინარე სტატუსი: {order.status})."
            )

        if order.is_reserved:
            if order.order_type == OrderType.BUY_LIMIT.value:
                refund_fiat = order.amount * order.target_price
                order.wallet.fiat_balance += refund_fiat

            elif order.order_type in (
                OrderType.SELL_LIMIT.value,
                OrderType.STOP_LOSS.value,
                OrderType.TAKE_PROFIT.value,
            ):
                asset = next(
                    (a for a in order.wallet.assets if a.symbol == order.symbol), None
                )
                if asset:
                    asset.amount += order.amount
                else:
                    new_asset = WalletAssetModel(
                        wallet_id=order.wallet_id,
                        symbol=order.symbol,
                        amount=order.amount,
                        average_buy_price=order.target_price,
                    )
                    self.db.add(new_asset)

        order.status = OrderStatus.CANCELLED.value
        self.db.commit()
        self.db.refresh(order)
        return Result.success(order)

    def get_orders(
        self, user_id: int, status_filter: Optional[str] = None
    ) -> List[OrderModel]:
        wallet = (
            self.db.query(WalletModel)
            .filter(WalletModel.user_id == user_id)
            .first()
        )
        if not wallet:
            return []

        query = self.db.query(OrderModel).filter(OrderModel.wallet_id == wallet.id)

        if status_filter and status_filter.upper() != "ALL":
            query = query.filter(OrderModel.status == status_filter.upper())

        return query.order_by(OrderModel.id.desc()).all()
