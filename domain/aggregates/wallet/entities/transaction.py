from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    id: Optional[int]
    wallet_id: int
    type: str
    amount: Decimal
    price: Decimal
    symbol: Optional[str] = None
    created_at: Optional[datetime] = None
