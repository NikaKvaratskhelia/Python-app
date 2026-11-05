from decimal import Decimal
from domain.aggregates.wallet.entities.wallet import Wallet
from domain.aggregates.wallet.entities.wallet_asset import WalletAsset
from domain.aggregates.wallet.entities.transaction import Transaction
from infrastructure.persistence.models.wallet_model import WalletModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.transaction_model import TransactionModel


class WalletMapper:
    @staticmethod
    def to_domain(model: WalletModel) -> Wallet:
        if not model:
            return None

        domain_assets = []
        if hasattr(model, "assets") and model.assets:
            asset: WalletAssetModel
            for asset in model.assets:
                domain_assets.append(
                    WalletAsset(
                        symbol=asset.symbol,
                        amount=Decimal(str(asset.amount)),
                        average_buy_price=Decimal(str(asset.average_buy_price)),
                    )
                )

        domain_transactions = []
        if hasattr(model, "transactions") and model.transactions:
            tx: TransactionModel
            for tx in model.transactions:
                domain_transactions.append(
                    Transaction(
                        id=tx.id,
                        wallet_id=tx.wallet_id,
                        type=tx.type,
                        amount=Decimal(str(tx.amount)),
                        price=Decimal(str(tx.price)),
                        symbol=tx.symbol,
                        created_at=tx.created_at,
                    )
                )

        return Wallet(
            id=model.id,
            user_id=model.user_id,
            fiat_balance=Decimal(str(model.fiat_balance)),
            assets=domain_assets,
            transactions=domain_transactions,
        )

    @staticmethod
    def to_persistence(domain: Wallet, model: WalletModel = None) -> WalletModel:
        if model is None:
            model = WalletModel(user_id=domain.user_id)

        model.fiat_balance = domain.fiat_balance
        return model
