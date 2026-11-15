import requests
from decimal import Decimal
from typing import Optional, Dict, Any


class MarketService:
    PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
    TICKER_24HR_URL = "https://api.binance.com/api/v3/ticker/24hr"

    @staticmethod
    def get_crypto_price(symbol: str) -> Optional[Decimal]:
        """მოაქვს კრიპტოვალუტის მიმდინარე ფასი (WebSocket ან Fallback REST)."""
        from services.binance_ws import BinanceWSManager

        ws_price = BinanceWSManager.get_price(symbol)
        if ws_price is not None and ws_price > Decimal("0"):
            return ws_price

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
            print(f"ქსელური შეცდომა: {e}")

        return None

    @staticmethod
    def get_market_stats(symbol: str) -> Optional[Dict[str, Any]]:
        """
        მოაქვს მიმდინარე ფასი და 24 საათიანი ცვლილების პროცენტი (% change)
        კონკრეტული სიმბოლოსთვის (WebSocket ან Fallback REST).
        """
        from services.binance_ws import BinanceWSManager

        ws_stats = BinanceWSManager.get_stats(symbol)
        if ws_stats and ws_stats.get("price", Decimal("0")) > Decimal("0"):
            return {
                "price": ws_stats["price"],
                "price_change_percent": ws_stats.get("change", Decimal("0")),
                "high": ws_stats.get("high"),
                "low": ws_stats.get("low"),
                "volume": ws_stats.get("volume"),
            }

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
        მოაქვს ყველა ხელმისაწვდომი წყვილის ფასი და 24სთ ცვლილება (WebSocket ან REST).
        აბრუნებს ლექსიკონს: {'BTC': {'price': Decimal, 'change': Decimal}, ...}
        """
        from services.binance_ws import BinanceWSManager

        ws_prices = BinanceWSManager.get_all_prices()
        if ws_prices:
            return {
                sym: {
                    "price": item["price"],
                    "change": item.get("change", Decimal("0")),
                }
                for sym, item in ws_prices.items()
            }

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

    @staticmethod
    def get_top_movers(limit: int = 5) -> dict:
        prices = MarketService.get_all_active_prices()
        if not prices:
            return {"gainers": [], "losers": []}

        sorted_items = sorted(
            prices.items(), key=lambda x: x[1]["change"], reverse=True
        )
        gainers = [
            {"symbol": sym, "price": info["price"], "change": info["change"]}
            for sym, info in sorted_items[:limit]
        ]
        losers = [
            {"symbol": sym, "price": info["price"], "change": info["change"]}
            for sym, info in sorted_items[-limit:][::-1]
        ]
        return {"gainers": gainers, "losers": losers}
