from dataclasses import dataclass
from typing import Literal, Optional, Dict

import numpy as np
import pandas as pd

from trading.services.rsi_calculator import get_rsi_for_symbol

Side = Literal["BUY", "SELL", "HOLD"]

@dataclass
class StrategyConfig:
    rsi_period: int = 2          # RSI(2): 초단기 모멘텀
    buy_thr: float = 10.0        # RSI가 이 값 미만이면 매수
    sell_thr: float = 70.0       # RSI가 이 값 초과면 매도
    max_positions: int = 10      # 보유 종목 상한
    per_trade_alloc_rate: float = 0.1  # 현금 대비 10%씩 배분
    min_qty: int = 1             # 최소 주문 수량
    use_profit_filter: bool = True  # RSI 매도 시, 이익 여부 확인
    stop_loss_rate: float = 0.08    # 손절 -8% (원치 않으면 0으로)

@dataclass
class Decision:
    symbol: str
    side: Side
    reason: str
    rsi: Optional[float]
    price: Optional[float]
    qty: int = 0

class Portfolio:
    """
    간단 포트폴리오 상태. 실제로는 DB(Positions 테이블)로 대체 권장.
    positions[symbol] = {"qty": int, "avg_price": float}
    """
    def __init__(self, cash: float, positions: Optional[Dict[str, Dict]] = None):
        self.cash = cash
        self.positions = positions or {}

    def holding(self, symbol: str) -> bool:
        p = self.positions.get(symbol)
        return bool(p and p["qty"] > 0)

    def avg_price(self, symbol: str) -> Optional[float]:
        p = self.positions.get(symbol)
        return p["avg_price"] if p else None

    def total_positions(self) -> int:
        return sum(1 for v in self.positions.values() if v["qty"] > 0)

def _latest_row(df: pd.DataFrame) -> Optional[pd.Series]:
    if df.empty:
        return None
    return df.iloc[-1]

def _calc_qty(price: float, cash: float, rate: float, min_qty: int) -> int:
    if price <= 0:
        return 0
    budget = cash * rate
    qty = int(budget // price)
    return max(qty, 0) if qty >= min_qty else 0

def decide(symbol: str, pf: Portfolio, cfg: StrategyConfig = StrategyConfig()) -> Decision:
    """
    - 입력: 종목, 현재 포트폴리오 현금/보유상태
    - 출력: BUY/SELL/HOLD 결정 + 근거
    """
    df = get_rsi_for_symbol(symbol, period=cfg.rsi_period)
    row = _latest_row(df)
    if row is None or np.isnan(row["RSI"]) or np.isnan(row["close"]):
        return Decision(symbol, "HOLD", "데이터 부족", None, None, 0)

    rsi = float(row["RSI"])
    price = float(row["close"])
    now_holding = pf.holding(symbol)

    # 손절/익절 우선 체크 (보유 중일 때만)
    if now_holding:
        avg = pf.avg_price(symbol)
        if avg and avg > 0:
            pnl_rate = (price - avg) / avg
            if cfg.stop_loss_rate > 0 and pnl_rate <= -cfg.stop_loss_rate:
                return Decision(symbol, "SELL", f"손절({pnl_rate:.2%})", rsi, price, qty=pf.positions[symbol]["qty"])

    # 매도 조건: 과매수 + (선택)수익 중
    if now_holding:
        avg = pf.avg_price(symbol)
        profit_ok = True if not cfg.use_profit_filter else (price > (avg or 0))
        if rsi > cfg.sell_thr and profit_ok:
            return Decision(symbol, "SELL", f"RSI>{cfg.sell_thr}" + (" & 이익" if cfg.use_profit_filter else ""), rsi, price, qty=pf.positions[symbol]["qty"])

    # 매수 조건: 과매도 & 포지션 한도
    if not now_holding:
        if pf.total_positions() >= cfg.max_positions:
            return Decision(symbol, "HOLD", "보유종목 상한", rsi, price, 0)
        if rsi < cfg.buy_thr:
            qty = _calc_qty(price, pf.cash, cfg.per_trade_alloc_rate, cfg.min_qty)
            if qty > 0:
                return Decision(symbol, "BUY", f"RSI<{cfg.buy_thr}", rsi, price, qty)

    return Decision(symbol, "HOLD", "조건 불충족", rsi, price, 0)