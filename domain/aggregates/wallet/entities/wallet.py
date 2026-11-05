from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from domain.aggregates.wallet.entities.wallet_asset import WalletAsset
from domain.aggregates.wallet.entities.transaction import Transaction


@dataclass
class Wallet:
    id: Optional[int]
    user_id: int
    fiat_balance: Decimal
    assets: List[WalletAsset] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)

    def deposit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("დეპოზიტის თანხა უნდა იყოს 0-ზე მეტი.")
        self.fiat_balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("გასატანი თანხა უნდა იყოს 0-ზე მეტი.")
        if self.fiat_balance < amount:
            raise ValueError("არასაკმარისი ფიატ ბალანსი საფულეში.")
        self.fiat_balance -= amount

    def buy_asset(self, symbol: str, amount: Decimal, price: Decimal) -> None:
        total_cost = amount * price
        self.withdraw(total_cost)

        existing_asset = next((a for a in self.assets if a.symbol == symbol), None)
        if existing_asset:
            existing_asset.update_on_buy(amount, price)
        else:
            self.assets.append(
                WalletAsset(symbol=symbol, amount=amount, average_buy_price=price)
            )

    def sell_asset(self, symbol: str, amount: Decimal, price: Decimal) -> None:
        existing_asset = next((a for a in self.assets if a.symbol == symbol), None)
        if not existing_asset or existing_asset.amount < amount:
            raise ValueError(f"საფულეში არ არის საკმარისი {symbol} გასაყიდად.")

        existing_asset.update_on_sell(amount)
        self.fiat_balance += amount * price
