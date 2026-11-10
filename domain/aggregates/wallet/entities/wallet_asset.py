from dataclasses import dataclass
from decimal import Decimal
from core.result import Result


@dataclass
class WalletAsset:
    symbol: str
    amount: Decimal
    average_buy_price: Decimal

    def update_on_buy(
        self, added_amount: Decimal, purchase_price: Decimal
    ) -> Result[None, str]:
        if added_amount <= 0:
            return Result.failure("რაოდენობა უნდა იყოს 0-ზე მეტი.")
        total_current_cost = self.amount * self.average_buy_price
        new_purchase_cost = added_amount * purchase_price

        self.amount += added_amount
        self.average_buy_price = (total_current_cost + new_purchase_cost) / self.amount
        return Result.success(None)

    def update_on_sell(self, sold_amount: Decimal) -> Result[None, str]:
        if sold_amount <= 0:
            return Result.failure("რაოდენობა უნდა იყოს 0-ზე მეტი.")
        if sold_amount > self.amount:
            return Result.failure("გაყიდვადი კრიპტოვალუტის რაოდენობა აღემატება ფლობილს.")

        self.amount -= sold_amount
        return Result.success(None)
