from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from core.database import get_db
from core.result import Result
from infrastructure.persistence.models.price_alert_model import PriceAlertModel


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        user_id: int,
        symbol: str,
        target_price: Decimal,
        condition: str,
    ) -> Result[PriceAlertModel, str]:
        symbol = symbol.strip().upper()
        if not symbol:
            return Result.failure("სიმბოლო არ შეიძლება იყოს ცარიელი.")

        if target_price <= Decimal("0"):
            return Result.failure("სამიზნე ფასი უნდა იყოს 0-ზე მეტი.")

        condition = condition.strip().upper()
        if condition not in ("ABOVE", "BELOW"):
            return Result.failure("პირობა უნდა იყოს 'ABOVE' ან 'BELOW'.")

        alert = PriceAlertModel(
            user_id=user_id,
            symbol=symbol,
            target_price=target_price,
            condition=condition,
            is_triggered=False,
        )
        with get_db(self.db) as db:
            db.add(alert)
        return Result.success(alert)

    def get_user_alerts(
        self, user_id: int, active_only: bool = True
    ) -> List[PriceAlertModel]:
        query = self.db.query(PriceAlertModel).filter(
            PriceAlertModel.user_id == user_id
        )
        if active_only:
            query = query.filter(PriceAlertModel.is_triggered == False)
        return query.order_by(PriceAlertModel.id.desc()).all()

    def get_triggered_alerts(self, user_id: int) -> Result[List[PriceAlertModel], str]:
        return Result.try_catch(
            lambda: self.db.query(PriceAlertModel)
            .filter(
                PriceAlertModel.user_id == user_id,
                PriceAlertModel.is_triggered == True,
            )
            .all(),
            error_mapper=lambda e: f"შეტყობინებების მიღების შეცდომა: {e}",
        )

    def delete_alert(self, alert_id: int, user_id: int) -> Result[None, str]:
        with get_db(self.db) as db:
            alert = (
                db.query(PriceAlertModel)
                .filter(
                    PriceAlertModel.id == alert_id, PriceAlertModel.user_id == user_id
                )
                .first()
            )
            if not alert:
                return Result.failure("შეტყობინება ვერ მოიძებნა.")

            db.delete(alert)
        return Result.success(None)

    @staticmethod
    def check_and_trigger_alerts(
        db: Session, market_prices: dict
    ) -> List[PriceAlertModel]:
        with get_db(db) as session:
            active_alerts = (
                session.query(PriceAlertModel)
                .filter(PriceAlertModel.is_triggered == False)
                .all()
            )
            triggered = []

            for alert in active_alerts:
                info = market_prices.get(alert.symbol)
                if not info:
                    continue

                current_price = info["price"]
                should_trigger = False

                if alert.condition == "ABOVE" and current_price >= alert.target_price:
                    should_trigger = True
                elif alert.condition == "BELOW" and current_price <= alert.target_price:
                    should_trigger = True

                if should_trigger:
                    alert.is_triggered = True
                    triggered.append(alert)

            return triggered
