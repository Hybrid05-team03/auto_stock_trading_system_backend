from dataclasses import dataclass
from typing import Literal


TradeSide = Literal["BUY", "SELL", "HOLD"]

@dataclass
class TradeSignalParam:
    """RSI 또는 기타 전략으로부터 생성된 매매 시그널"""
    symbol: str
    side: TradeSide
    reason: str
    rsi: float
    price: float
    quantity: int = 0