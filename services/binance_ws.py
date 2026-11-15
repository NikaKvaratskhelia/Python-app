import asyncio
import json
import logging
import threading
from decimal import Decimal
from typing import Dict, Any, Optional
import websockets

logger = logging.getLogger(__name__)


class BinanceWSManager:
    WS_URL = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
    _latest_prices: Dict[str, Dict[str, Any]] = {}
    _lock = threading.Lock()
    _running = False
    _thread: Optional[threading.Thread] = None

    @classmethod
    def get_price(cls, symbol: str) -> Optional[Decimal]:
        sym = symbol.strip().upper()
        if sym.endswith("USDT"):
            sym = sym[:-4]
        with cls._lock:
            data = cls._latest_prices.get(sym)
            return data["price"] if data else None

    @classmethod
    def get_stats(cls, symbol: str) -> Optional[Dict[str, Any]]:
        sym = symbol.strip().upper()
        if sym.endswith("USDT"):
            sym = sym[:-4]
        with cls._lock:
            data = cls._latest_prices.get(sym)
            return dict(data) if data else None

    @classmethod
    def get_all_prices(cls) -> Dict[str, Dict[str, Any]]:
        with cls._lock:
            return dict(cls._latest_prices)

    @classmethod
    async def _stream_loop(cls):
        while cls._running:
            try:
                async with websockets.connect(cls.WS_URL, ping_interval=20, ping_timeout=20) as ws:
                    logger.info("Binance WebSocket დაკავშირდა წარმატებით.")
                    while cls._running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        with cls._lock:
                            for item in data:
                                raw_symbol = item.get("s", "")
                                if raw_symbol.endswith("USDT"):
                                    base = raw_symbol[:-4]
                                    price = Decimal(str(item.get("c", "0")))
                                    open_p = Decimal(str(item.get("o", "0")))
                                    change = (
                                        ((price - open_p) / open_p * 100)
                                        if open_p > Decimal("0")
                                        else Decimal("0")
                                    )
                                    cls._latest_prices[base] = {
                                        "price": price,
                                        "open": open_p,
                                        "change": change,
                                        "high": Decimal(str(item.get("h", "0"))),
                                        "low": Decimal(str(item.get("l", "0"))),
                                        "volume": Decimal(str(item.get("v", "0"))),
                                    }
            except Exception as e:
                logger.warning(f"Binance WS კავშირი გაწყდა ({e}), თავიდან ცდა 2 წამში...")
                await asyncio.sleep(2)

    @classmethod
    def _run_worker(cls):
        asyncio.run(cls._stream_loop())

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._thread = threading.Thread(target=cls._run_worker, daemon=True)
        cls._thread.start()

    @classmethod
    def stop(cls):
        cls._running = False
