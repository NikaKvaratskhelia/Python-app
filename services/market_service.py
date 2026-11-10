import requests
from decimal import Decimal
from typing import Optional, Dict, Any


class MarketService:
    PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
    TICKER_24HR_URL = "https://api.binance.com/api/v3/ticker/24hr"

    @staticmethod
    def get_crypto_price(symbol: str) -> Optional[Decimal]:
        """მოაქვს კრიპტოვალუტის მიმდინარე ფასი Binance-დან."""

        formatted_symbol = symbol.upper().strip()

        if not formatted_symbol.endswith("USDT"):
            formatted_symbol += "USDT"

        try:
            response = requests.get(
                MarketService.PRICE_URL, params={"symbol": formatted_symbol}, timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data["price"]))

        except requests.exceptions.RequestException as e:
            print(f"❌ ქსელური შეცდომა: {e}")

        return None

    @staticmethod
    def get_market_stats(symbol: str) -> Optional[Dict[str, Any]]:
        """
        მოაქვს მიმდინარე ფასი და 24 საათიანი ცვლილების პროცენტი (% change)
        კონკრეტული სიმბოლოსთვის (მაგ: 'BTC' -> 'BTCUSDT')
        """

        formatted_symbol = symbol.upper().strip()

        if not formatted_symbol.endswith("USDT"):
            formatted_symbol += "USDT"

        try:
            response = requests.get(
                MarketService.TICKER_24HR_URL,
                params={"symbol": formatted_symbol},
                timeout=5,
            )

            if response.status_code == 200:

                data = response.json()

                return {
                    "price": Decimal(str(data["lastPrice"])),
                    "price_change_percent": Decimal(str(data["priceChangePercent"])),
                }

        except requests.exceptions.RequestException as e:
            print(f"ქსელური შეცდომა საბაზრო სტატისტიკის წამოღებისას: {e}")

        return None

    @staticmethod
    def get_all_active_prices() -> dict[str, dict[str, Any]]:
        """
        მოაქვს ყველა ხელმისაწვდომი წყვილის ფასი და 24სთ ცვლილება Binance-დან.
        აბრუნებს ლექსიკონს: {'BTC': {'price': Decimal, 'change': Decimal}, ...}
        """

        try:

            response = requests.get(MarketService.TICKER_24HR_URL, timeout=10)

            if response.status_code == 200:

                result = {}

                for item in response.json():
                    sym = item["symbol"]

                    if sym.endswith("USDT"):
                        base_symbol = sym[:-4]

                        result[base_symbol] = {
                            "price": Decimal(str(item["lastPrice"])),
                            "change": Decimal(str(item["priceChangePercent"])),
                        }

                return result

        except requests.exceptions.RequestException as e:
            print(f"ვეღარ მოხერხდა ბაზრის მონაცემების მიღება: {e}")

        return {}
