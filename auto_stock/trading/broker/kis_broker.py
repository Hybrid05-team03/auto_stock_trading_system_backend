from dataclasses import dataclass
from typing import Optional

@dataclass
class OrderResult:
    ok: bool
    order_id: Optional[str]
    message: str

# TODO: 실제 KIS 주문 API로 교체
class Broker:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def buy_market(self, symbol: str, qty: int) -> OrderResult:
        if self.dry_run:
            return OrderResult(True, "SIM-ORDER-BUY", f"[DRY] BUY {symbol} x {qty} @MKT")
        # TODO: KIS 주문 API 호출
        return OrderResult(False, None, "실주문 미구현")

    def sell_market(self, symbol: str, qty: int) -> OrderResult:
        if self.dry_run:
            return OrderResult(True, "SIM-ORDER-SELL", f"[DRY] SELL {symbol} x {qty} @MKT")
        # TODO: KIS 주문 API 호출
        return OrderResult(False, None, "실주문 미구현")