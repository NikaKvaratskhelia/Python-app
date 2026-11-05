from decimal import Decimal
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories.wallet_repository import WalletRepository
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from domain.aggregates.wallet.entities.wallet import Wallet


class WalletService:
    def __init__(self, db: Session):
        self.db = db
        self.wallet_repo = WalletRepository(db)

    def get_or_create_wallet(self, user_id: int) -> Wallet:
        wallet = self.wallet_repo.get_by_user_id(user_id)
        if not wallet:
            new_wallet = Wallet(
                id=None,
                user_id=user_id,
                fiat_balance=Decimal("10000.00"),
            )
            self.wallet_repo.save(new_wallet)
            wallet = self.wallet_repo.get_by_user_id(user_id)
        return wallet

    def deposit(self, user_id: int, amount: Decimal) -> Wallet:
        wallet = self.get_or_create_wallet(user_id)
        wallet.deposit(amount)

        updated_wallet = self.wallet_repo.save(wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="DEPOSIT",
            amount=amount,
            price=Decimal("1.00"),
            symbol="USD",
        )
        self.db.add(tx)
        return updated_wallet

    def buy_asset(
        self, user_id: int, symbol: str, amount: Decimal, price: Decimal
    ) -> Wallet:
        wallet = self.get_or_create_wallet(user_id)

        wallet.buy_asset(symbol, amount, price)

        updated_wallet = self.wallet_repo.save(wallet)
        self._sync_persistence_assets(updated_wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="BUY",
            amount=amount,
            price=price,
            symbol=symbol,
        )
        self.db.add(tx)
        return updated_wallet

    def sell_asset(
        self, user_id: int, symbol: str, amount: Decimal, price: Decimal
    ) -> Wallet:
        wallet = self.get_or_create_wallet(user_id)

        wallet.sell_asset(symbol, amount, price)

        updated_wallet = self.wallet_repo.save(wallet)
        self._sync_persistence_assets(updated_wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="SELL",
            amount=amount,
            price=price,
            symbol=symbol,
        )
        self.db.add(tx)
        return updated_wallet

    def _sync_persistence_assets(self, domain_wallet: Wallet):
        existing_models = (
            self.db.query(WalletAssetModel)
            .filter(WalletAssetModel.wallet_id == domain_wallet.id)
            .all()
        )
        existing_dict = {m.symbol: m for m in existing_models}

        for domain_asset in domain_wallet.assets:
            if domain_asset.symbol in existing_dict:
                model = existing_dict[domain_asset.symbol]
                model.amount = domain_asset.amount
                model.average_buy_price = domain_asset.average_buy_price
            else:
                new_model = WalletAssetModel(
                    wallet_id=domain_wallet.id,
                    symbol=domain_asset.symbol,
                    amount=domain_asset.amount,
                    average_buy_price=domain_asset.average_buy_price,
                )
                self.db.add(new_model)
