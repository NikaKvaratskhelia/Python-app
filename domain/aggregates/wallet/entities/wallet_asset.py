from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class WalletAsset:
    symbol: str
    amount: Decimal
    average_buy_price: Decimal

    def update_on_buy(self, added_amount: Decimal, purchase_price: Decimal):
        total_current_cost = self.amount * self.average_buy_price
        new_purchase_cost = added_amount * purchase_price

        self.amount += added_amount
        self.average_buy_price = (total_current_cost + new_purchase_cost) / self.amount

    def update_on_sell(self, sold_amount: Decimal):
        if sold_amount > self.amount:
            raise ValueError("გაყიდვადი კრიპტოვალუტის რაოდენობა აღემატება ფლობილს.")
        
        self.amount -= sold_amount
