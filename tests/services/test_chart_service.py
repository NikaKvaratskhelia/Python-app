from decimal import Decimal
from services.chart_service import ChartService


def test_render_sparkline():
    prices = [Decimal(p) for p in [100, 105, 110, 120, 115, 130, 140]]
    sparkline = ChartService.render_sparkline(prices)
    assert len(sparkline) == len(prices)
    assert sparkline[0] == ChartService.BLOCKS[0]  # lowest
    assert sparkline[-1] == ChartService.BLOCKS[7]  # highest


def test_render_sparkline_flat():
    prices = [Decimal("100.00")] * 5
    sparkline = ChartService.render_sparkline(prices)
    assert len(sparkline) == 5


def test_render_ascii_chart():
    prices = [Decimal(p) for p in [50, 60, 55, 70, 80, 75, 90]]
    chart_lines = ChartService.render_ascii_chart(prices, height=5, width=7)
    assert len(chart_lines) >= 6  # 5 rows + axis
    assert "$" in chart_lines[0]
    assert "─" in chart_lines[-1]


def test_get_chart_data():
    data = ChartService.get_chart_data("BTC", interval="1h", limit=12)
    assert data["symbol"] == "BTC"
    assert data["candles_count"] == 12
    assert data["high"] >= data["low"]
    assert "chart_lines" in data
    assert "sparkline" in data
