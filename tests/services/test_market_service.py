from decimal import Decimal
from unittest.mock import MagicMock
import requests
from services.market_service import MarketService


def test_get_crypto_price_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"symbol": "BTCUSDT", "price": "65432.10"}

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    price = MarketService.get_crypto_price("BTC")
    assert price == Decimal("65432.10")


def test_get_crypto_price_failure(monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Connection error")

    monkeypatch.setattr(requests, "get", mock_get)

    price = MarketService.get_crypto_price("BTC")
    assert price is None


def test_get_market_stats_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "symbol": "ETHUSDT",
        "lastPrice": "3450.00",
        "priceChangePercent": "5.25",
    }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    stats = MarketService.get_market_stats("ETH")
    assert stats is not None
    assert stats["price"] == Decimal("3450.00")
    assert stats["price_change_percent"] == Decimal("5.25")


def test_get_all_active_prices(monkeypatch):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"symbol": "BTCUSDT", "lastPrice": "60000", "priceChangePercent": "2.5"},
        {"symbol": "ETHUSDT", "lastPrice": "3000", "priceChangePercent": "-1.2"},
        {"symbol": "BNBBTC", "lastPrice": "0.005", "priceChangePercent": "0.0"},
    ]

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_response)

    all_prices = MarketService.get_all_active_prices()
    assert "BTC" in all_prices
    assert all_prices["BTC"]["price"] == Decimal("60000")
    assert "ETH" in all_prices
    assert all_prices["ETH"]["price"] == Decimal("3000")
    assert "BNB" not in all_prices  # Only USDT pairs
