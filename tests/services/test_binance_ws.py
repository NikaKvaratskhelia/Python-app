from decimal import Decimal
from services.binance_ws import BinanceWSManager


def test_binance_ws_manager_prices():
    try:
        with BinanceWSManager._lock:
            BinanceWSManager._latest_prices["TESTCOIN"] = {
                "price": Decimal("65000.50"),
                "open": Decimal("64000.00"),
                "change": Decimal("1.56"),
                "high": Decimal("66000.00"),
                "low": Decimal("63000.00"),
                "volume": Decimal("15000.00"),
            }

        # Test get_price with and without USDT
        assert BinanceWSManager.get_price("TESTCOIN") == Decimal("65000.50")
        assert BinanceWSManager.get_price("TESTCOINUSDT") == Decimal("65000.50")
        assert BinanceWSManager.get_price("testcoin") == Decimal("65000.50")
        assert BinanceWSManager.get_price("NON_EXISTENT") is None

        # Test get_stats
        stats = BinanceWSManager.get_stats("TESTCOIN")
        assert stats is not None
        assert stats["price"] == Decimal("65000.50")
        assert stats["change"] == Decimal("1.56")

        # Test get_all_prices
        all_p = BinanceWSManager.get_all_prices()
        assert "TESTCOIN" in all_p
        assert all_p["TESTCOIN"]["price"] == Decimal("65000.50")
    finally:
        with BinanceWSManager._lock:
            BinanceWSManager._latest_prices.clear()
