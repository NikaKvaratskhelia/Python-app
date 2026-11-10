from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from domain.aggregates.wallet.entities.wallet_asset import WalletAsset
from domain.aggregates.wallet.entities.transaction import Transaction
from core.result import Result


@dataclass
class Wallet:
    id: Optional[int]
    user_id: int
    fiat_balance: Decimal
    assets: List[WalletAsset] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)

    def deposit(self, amount: Decimal) -> Result[Decimal, str]:
        if amount <= 0:
            return Result.failure("დეპოზიტის თანხა უნდა იყოს 0-ზე მეტი.")
        self.fiat_balance += amount
        return Result.success(self.fiat_balance)

    def withdraw(self, amount: Decimal) -> Result[Decimal, str]:
        if amount <= 0:
            return Result.failure("გასატანი თანხა უნდა იყოს 0-ზე მეტი.")
        
        if self.fiat_balance < amount:
            return Result.failure("არასაკმარისი ბალანსი საფულეში.")
        
        self.fiat_balance -= amount
        return Result.success(self.fiat_balance)

    def buy_asset(
        self, symbol: str, amount: Decimal, price: Decimal
    ) -> Result[None, str]:
        if amount <= 0:
            return Result.failure("რაოდენობა უნდა იყოს 0-ზე მეტი.")
        if price <= 0:
            return Result.failure("ფასი უნდა იყოს 0-ზე მეტი.")

        total_cost = amount * price
        withdraw_result = self.withdraw(total_cost)
        if withdraw_result.is_failure:
            return withdraw_result

        existing_asset = next((a for a in self.assets if a.symbol == symbol), None)
        if existing_asset:
            update_result = existing_asset.update_on_buy(amount, price)
            if update_result.is_failure:
                return update_result
        else:
            self.assets.append(
                WalletAsset(symbol=symbol, amount=amount, average_buy_price=price)
            )
        return Result.success(None)

    def sell_asset(
        self, symbol: str, amount: Decimal, price: Decimal
    ) -> Result[None, str]:
        if amount <= 0:
            return Result.failure("რაოდენობა უნდა იყოს 0-ზე მეტი.")
        if price <= 0:
            return Result.failure("ფასი უნდა იყოს 0-ზე მეტი.")

        existing_asset = next((a for a in self.assets if a.symbol == symbol), None)
        if not existing_asset or existing_asset.amount < amount:
            return Result.failure(f"საფულეში არ არის საკმარისი {symbol} გასაყიდად.")

        update_result = existing_asset.update_on_sell(amount)
        if update_result.is_failure:
            return update_result

        self.fiat_balance += amount * price
        return Result.success(None)
