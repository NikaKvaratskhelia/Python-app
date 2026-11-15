from sqlalchemy.orm import Session, joinedload
from domain.aggregates.wallet.entities.wallet import Wallet
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.mappers.wallet_mapper import WalletMapper
from core.database import get_db


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Wallet | None:
        model = (
            self.db.query(WalletModel)
            .options(joinedload(WalletModel.assets))
            .filter(WalletModel.user_id == user_id)
            .first()
        )
        return WalletMapper.to_domain(model)

    def save(self, wallet: Wallet) -> Wallet:
        with get_db(self.db) as db:
            model = (
                db.query(WalletModel)
                .filter(WalletModel.user_id == wallet.user_id)
                .first()
            )

            if not model:
                model = WalletModel(
                    user_id=wallet.user_id, fiat_balance=wallet.fiat_balance
                )
                db.add(model)
            else:
                model.fiat_balance = wallet.fiat_balance

        return WalletMapper.to_domain(model)
