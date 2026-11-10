from decimal import Decimal
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories.wallet_repository import WalletRepository
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from domain.aggregates.wallet.entities.wallet import Wallet
from services.market_service import MarketService
from core.result import Result


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

    def deposit(self, user_id: int, amount: Decimal) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        deposit_result = wallet.deposit(amount)
        if deposit_result.is_failure:
            return Result.failure(deposit_result.error)

        updated_wallet = self.wallet_repo.save(wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="DEPOSIT",
            amount=amount,
            price=Decimal("1.00"),
            symbol="USD",
        )

        self.db.add(tx)

        return Result.success(updated_wallet)

    def buy_asset(
        self, user_id: int, symbol: str, amount: Decimal, price: Decimal
    ) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        buy_result = wallet.buy_asset(symbol, amount, price)
        if buy_result.is_failure:
            return Result.failure(buy_result.error)

        updated_wallet = self.wallet_repo.save(wallet)
        self._sync_persistence_assets(wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="BUY",
            amount=amount,
            price=price,
            symbol=symbol,
        )

        self.db.add(tx)
        self.db.flush()

        saved_wallet = self.wallet_repo.get_by_user_id(user_id)
        return Result.success(saved_wallet)

    def sell_asset(
        self, user_id: int, symbol: str, amount: Decimal, price: Decimal
    ) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        sell_result = wallet.sell_asset(symbol, amount, price)
        if sell_result.is_failure:
            return Result.failure(sell_result.error)

        updated_wallet = self.wallet_repo.save(wallet)
        self._sync_persistence_assets(wallet)

        tx = TransactionModel(
            wallet_id=updated_wallet.id,
            type="SELL",
            amount=amount,
            price=price,
            symbol=symbol,
        )

        self.db.add(tx)
        self.db.flush()

        saved_wallet = self.wallet_repo.get_by_user_id(user_id)
        return Result.success(saved_wallet)

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

    def get_portfolio_summary(self, user_id: int) -> dict:
        """
        ითვლის საფულის სრულ პორტფოლიოს: ბალანსს, აქტივების საბაზრო ღირებულებას,
        მთლიან ინვესტიციას და მოგება-ზარალს (PnL).
        """

        wallet = self.get_or_create_wallet(user_id)
        market_prices = MarketService.get_all_active_prices()

        total_crypto_value = Decimal("0.00")
        total_invested_crypto = Decimal("0.00")
        assets_details = []

        for asset in wallet.assets:
            market_info = market_prices.get(asset.symbol)

            current_price = (
                market_info["price"] if market_info else asset.average_buy_price
            )

            current_value = asset.amount * current_price
            invested_amount = asset.amount * asset.average_buy_price

            pnl_usd = current_value - invested_amount

            pnl_percent = (
                (
                    (current_price - asset.average_buy_price)
                    / asset.average_buy_price
                    * 100
                )
                if asset.average_buy_price > 0
                else Decimal("0.00")
            )

            total_crypto_value += current_value
            total_invested_crypto += invested_amount

            assets_details.append(
                {
                    "symbol": asset.symbol,
                    "amount": asset.amount,
                    "average_buy_price": asset.average_buy_price,
                    "current_price": current_price,
                    "current_value": current_value,
                    "pnl_usd": pnl_usd,
                    "pnl_percent": pnl_percent,
                }
            )

        total_portfolio_value = wallet.fiat_balance + total_crypto_value

        return {
            "fiat_balance": wallet.fiat_balance,
            "total_crypto_value": total_crypto_value,
            "total_portfolio_value": total_portfolio_value,
            "assets": assets_details,
        }
