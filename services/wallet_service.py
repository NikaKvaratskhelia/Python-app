import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlalchemy.orm import Session
from core.database import get_db
from infrastructure.persistence.repositories.wallet_repository import WalletRepository
from infrastructure.persistence.models.transaction_model import TransactionModel
from infrastructure.persistence.models.wallet_asset import WalletAssetModel
from infrastructure.persistence.models.user_model import UserModel
from domain.aggregates.wallet.entities.wallet import Wallet
from domain.aggregates.wallet.entities.wallet_asset import WalletAsset
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

        with get_db(self.db) as db:
            updated_wallet = self.wallet_repo.save(wallet)

            tx = TransactionModel(
                wallet_id=updated_wallet.id,
                type="DEPOSIT",
                amount=amount,
                price=Decimal("1.00"),
                symbol="USD",
            )
            db.add(tx)

        return Result.success(updated_wallet)

    def buy_asset(
        self,
        user_id: int,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0.00"),
    ) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        total_needed = (amount * price) + fee
        if wallet.fiat_balance < total_needed:
            return Result.failure(
                f"არასაკმარისი ბალანსი. საჭიროა: ${total_needed:,.2f} (საკომისიოს ჩათვლით), ხელმისაწვდომია: ${wallet.fiat_balance:,.2f}."
            )

        buy_result = wallet.buy_asset(symbol, amount, price)
        if buy_result.is_failure:
            return Result.failure(buy_result.error)

        if fee > Decimal("0"):
            wallet.fiat_balance -= fee

        with get_db(self.db) as db:
            updated_wallet = self.wallet_repo.save(wallet)
            self._sync_persistence_assets(wallet)

            tx = TransactionModel(
                wallet_id=updated_wallet.id,
                type="BUY",
                amount=amount,
                price=price,
                symbol=symbol,
            )
            db.add(tx)

            if fee > Decimal("0"):
                fee_tx = TransactionModel(
                    wallet_id=updated_wallet.id,
                    type="FEE",
                    amount=fee,
                    price=Decimal("1.00"),
                    symbol="USD",
                )
                db.add(fee_tx)

        saved_wallet = self.wallet_repo.get_by_user_id(user_id)
        return Result.success(saved_wallet)

    def sell_asset(
        self,
        user_id: int,
        symbol: str,
        amount: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0.00"),
    ) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        sell_result = wallet.sell_asset(symbol, amount, price)
        if sell_result.is_failure:
            return Result.failure(sell_result.error)

        if fee > Decimal("0"):
            wallet.fiat_balance -= fee

        with get_db(self.db) as db:
            updated_wallet = self.wallet_repo.save(wallet)
            self._sync_persistence_assets(wallet)

            tx = TransactionModel(
                wallet_id=updated_wallet.id,
                type="SELL",
                amount=amount,
                price=price,
                symbol=symbol,
            )
            db.add(tx)

            if fee > Decimal("0"):
                fee_tx = TransactionModel(
                    wallet_id=updated_wallet.id,
                    type="FEE",
                    amount=fee,
                    price=Decimal("1.00"),
                    symbol="USD",
                )
                db.add(fee_tx)

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

    def withdraw(self, user_id: int, amount: Decimal) -> Result[Wallet, str]:
        wallet = self.get_or_create_wallet(user_id)

        withdraw_result = wallet.withdraw(amount)
        if withdraw_result.is_failure:
            return Result.failure(withdraw_result.error)

        with get_db(self.db) as db:
            updated_wallet = self.wallet_repo.save(wallet)

            tx = TransactionModel(
                wallet_id=updated_wallet.id,
                type="WITHDRAW",
                amount=amount,
                price=Decimal("1.00"),
                symbol="USD",
            )
            db.add(tx)

        return Result.success(updated_wallet)

    def transfer(
        self,
        sender_user_id: int,
        receiver_username: str,
        asset_symbol: str,
        amount: Decimal,
    ) -> Result[dict, str]:
        if amount <= Decimal("0"):
            return Result.failure("გადასარიცხი რაოდენობა უნდა იყოს 0-ზე მეტი.")

        asset_symbol = asset_symbol.strip().upper()

        receiver_user = (
            self.db.query(UserModel)
            .filter(UserModel.username == receiver_username.strip())
            .first()
        )
        
        if not receiver_user:
            return Result.failure(
                f"მიმღები მომხმარებელი '{receiver_username}' ვერ მოიძებნა."
            )

        if receiver_user.id == sender_user_id:
            return Result.failure("საკუთარ თავზე გადარიცხვა დაუშვებელია.")

        sender_wallet = self.get_or_create_wallet(sender_user_id)
        receiver_wallet = self.get_or_create_wallet(receiver_user.id)

        if asset_symbol == "USD":
            if sender_wallet.fiat_balance < amount:
                return Result.failure(
                    f"არასაკმარისი ბალანსი. ხელმისაწვდომია: ${sender_wallet.fiat_balance:,.2f}, საჭიროა: ${amount:,.2f}."
                )

            with get_db(self.db) as db:
                sender_wallet.fiat_balance -= amount
                receiver_wallet.fiat_balance += amount
                self.wallet_repo.save(sender_wallet)
                self.wallet_repo.save(receiver_wallet)

                tx_out = TransactionModel(
                    wallet_id=sender_wallet.id,
                    type="TRANSFER_OUT",
                    amount=amount,
                    price=Decimal("1.00"),
                    symbol="USD",
                )
                
                tx_in = TransactionModel(
                    wallet_id=receiver_wallet.id,
                    type="TRANSFER_IN",
                    amount=amount,
                    price=Decimal("1.00"),
                    symbol="USD",
                )
                
                db.add(tx_out)
                db.add(tx_in)

            return Result.success(
                {
                    "symbol": "USD",
                    "amount": amount,
                    "receiver": receiver_username,
                }
            )
        else:
            sender_asset = next(
                (a for a in sender_wallet.assets if a.symbol == asset_symbol),
                None,
            )
            available = sender_asset.amount if sender_asset else Decimal("0")

            if not sender_asset or available < amount:
                return Result.failure(
                    f"არასაკმარისი {asset_symbol} აქტივი. ხელმისაწვდომია: {available}, საჭიროა: {amount}."
                )

            with get_db(self.db) as db:
                sender_asset.amount -= amount
                self.wallet_repo.save(sender_wallet)
                self._sync_persistence_assets(sender_wallet)

                receiver_asset = next(
                    (a for a in receiver_wallet.assets if a.symbol == asset_symbol),
                    None,
                )
                avg_price = sender_asset.average_buy_price
                if receiver_asset:
                    receiver_asset.update_on_buy(amount, avg_price)
                else:
                    receiver_wallet.assets.append(
                        WalletAsset(
                            symbol=asset_symbol,
                            amount=amount,
                            average_buy_price=avg_price,
                        )
                    )

                self.wallet_repo.save(receiver_wallet)
                self._sync_persistence_assets(receiver_wallet)

                tx_out = TransactionModel(
                    wallet_id=sender_wallet.id,
                    type="TRANSFER_OUT",
                    amount=amount,
                    price=avg_price,
                    symbol=asset_symbol,
                )
                
                tx_in = TransactionModel(
                    wallet_id=receiver_wallet.id,
                    type="TRANSFER_IN",
                    amount=amount,
                    price=avg_price,
                    symbol=asset_symbol,
                )
                
                db.add(tx_out)
                db.add(tx_in)

            return Result.success(
                {
                    "symbol": asset_symbol,
                    "amount": amount,
                    "receiver": receiver_username,
                }
            )

    def export_transactions_csv(
        self, user_id: int, directory: str = "exports"
    ) -> Result[str, str]:
        wallet = self.get_or_create_wallet(user_id)
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        username = user_model.username if user_model else f"user_{user_id}"

        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"transactions_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        filepath = out_dir / filename

        def _write_csv() -> str:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "ID",
                        "Timestamp",
                        "Type",
                        "Symbol",
                        "Amount",
                        "Unit Price ($)",
                        "Total USD",
                    ]
                )

                for tx in wallet.transactions or []:
                    total_usd = (tx.amount * tx.price) if tx.price else tx.amount
                    time_str = (
                        tx.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(tx.created_at, "strftime")
                        else str(tx.created_at)
                    )
                    writer.writerow(
                        [
                            tx.id,
                            time_str,
                            tx.type,
                            tx.symbol or "USD",
                            str(tx.amount),
                            f"{tx.price:.2f}" if tx.price else "-",
                            f"{total_usd:.2f}",
                        ]
                    )

            return str(filepath.resolve())

        return Result.try_catch(
            _write_csv,
            error_mapper=lambda e: f"ფაილის ექსპორტის შეცდომა: {e}",
        )

    def get_advanced_portfolio_analytics(self, user_id: int) -> dict:
        summary = self.get_portfolio_summary(user_id)
        total_val = summary["total_portfolio_value"]

        allocations = []
        if total_val > 0:
            fiat_pct = (summary["fiat_balance"] / total_val) * 100
            allocations.append(
                {
                    "asset": "USD",
                    "amount": summary["fiat_balance"],
                    "value": summary["fiat_balance"],
                    "percent": fiat_pct,
                }
            )

            for a in summary["assets"]:
                pct = (a["current_value"] / total_val) * 100
                allocations.append(
                    {
                        "asset": a["symbol"],
                        "amount": a["amount"],
                        "value": a["current_value"],
                        "percent": pct,
                    }
                )
        else:
            allocations.append(
                {
                    "asset": "USD",
                    "amount": Decimal("0.00"),
                    "value": Decimal("0.00"),
                    "percent": Decimal("100.00"),
                }
            )

        unrealized_pnl = sum((a["pnl_usd"] for a in summary["assets"]), Decimal("0.00"))

        return {
            "summary": summary,
            "allocations": allocations,
            "unrealized_pnl": unrealized_pnl,
        }
