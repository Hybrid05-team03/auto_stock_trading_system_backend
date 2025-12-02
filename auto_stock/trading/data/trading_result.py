from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class TradeResult:
    """주문 결과 반환 형식"""
    ok: bool
    side: Literal["BUY", "SELL"]
    symbol: str
    qty: int
    price: int
    order_type: Literal["limit", "market"]
    order_id: Optional[str] = None
    message: str = ""

