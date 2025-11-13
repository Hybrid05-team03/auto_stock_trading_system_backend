import time
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict

from trading.services.rsi_calculator import calculate_rsi, get_rsi_for_symbol
from kis.api.price import kis_get_realtime_price
from kis.api.quote import kis_get_last_quota
from kis.websocket.trading_ws import KISTRADING
from trading.data.trade_data import TradeSignalParam

trader = KISTRADING(dry_run=False)
# ----------------------------
# 포트폴리오 상태 관리
# ----------------------------
class Portfolio:
    def __init__(self, cash: float, positions: Optional[Dict[str, Dict]] = None):
        self.cash = cash
        self.positions = positions or {}

    def is_holding(self, symbol: str) -> bool:
        pos = self.positions.get(symbol)
        return bool(pos and pos["qty"] > 0)

    def avg_price(self, symbol: str) -> Optional[float]:
        pos = self.positions.get(symbol)
        return pos["avg_price"] if pos else None

    def active_count(self) -> int:
        return sum(1 for p in self.positions.values() if p["qty"] > 0)

# ----------------------------
# RSI 시그널 계산
# ----------------------------
def get_static_signal(symbol: str, period: int = 2) -> dict:
    df = get_rsi_for_symbol(symbol, period)
    if df.empty:
        return {"symbol": symbol, "action": "HOLD", "reason": "데이터 없음"}

    latest = df.iloc[-1]
    rsi, price = latest["RSI"], latest["close"]

    if rsi < 30:
        return {"symbol": symbol, "action": "BUY", "rsi": rsi, "price": price, "reason": "RSI 과매도"}
    elif rsi > 70:
        return {"symbol": symbol, "action": "SELL", "rsi": rsi, "price": price, "reason": "RSI 과매수"}
    else:
        return {"symbol": symbol, "action": "HOLD", "rsi": rsi, "price": price, "reason": "보합 구간"}

# ----------------------------
# RSI 신호 기반 의사결정
# ----------------------------
def evaluate_signal(symbol: str, price: float, df: pd.DataFrame, rsi_period: int = 2) -> tuple[TradeSignalParam, pd.DataFrame]:

    updated_df = pd.concat([df, pd.DataFrame([{"date": datetime.now(), "close": price}])], ignore_index=True).tail(100)
    rsi_series = calculate_rsi(updated_df, period=rsi_period).ffill()
    rsi = float(rsi_series.iloc[-1])

    if rsi < 5:
        side, reason = "BUY", f"RSI={rsi:.2f} < 5"
    elif rsi > 80:
        side, reason = "SELL", f"RSI={rsi:.2f} > 80"
    else:
        side, reason = "HOLD", f"RSI={rsi:.2f}"

    return TradeSignalParam(symbol, side, reason, rsi, price), updated_df

# ----------------------------
# 시장 데이터 조회
# ----------------------------
## KIS: 과거 시세 조회 (기본 : 100일분의 데이터 조회)
def get_recent_prices(symbol: str, count: int = 100) -> pd.DataFrame:
    df = kis_get_last_quota(symbol, count=count)
    return df[["date", "close"]].tail(count)

## KIS: 실시간 시세 조회
def get_current_price(symbol: str) -> float:
    return kis_get_realtime_price(symbol)

# ----------------------------
# 자동매매 루프
# ----------------------------
def auto_trade(symbol: str):
    print(f"[START] 종목 코드 {symbol} 자동매매 시작")

    # 과거 시세 데이터
    last_price = get_recent_prices(symbol)
    while True:
        # 실시간 주가 데이터
        current_price = get_current_price(symbol)
        if np.isnan(current_price):
            print(f"[WARN] : 종목 코드 {symbol} 시세가 조회되지 않음")
            time.sleep(5)
            continue

        current_price, last_price = evaluate_signal(symbol, current_price, last_price)
        print(f"[{symbol}] {current_price.reason}, Price={current_price}")

        time.sleep(10)


# ---------------------------------------------------------
# 실시간 시세 기반 자동매매 (핸들러)
# ---------------------------------------------------------
async def handle_realtime_price(symbol: str, tick_data: dict, df_cache: Dict[str, pd.DataFrame]):
    try:
        # 실시간 체결가 추출
        price = float(tick_data["stck_prpr"])

        # 기존 데이터프레임 가져오기
        df = df_cache.get(symbol, get_recent_prices(symbol, count=100))

        # RSI 계산 및 매매 판단
        decision, updated_df = evaluate_signal(symbol, price, df)
        df_cache[symbol] = updated_df

        print(f"[{symbol}] {decision.reason}, Price={price}")

        # 주문 실행 (BUY or SELL)
        if decision.side in ("BUY", "SELL"):
            result = trader.place_order(symbol=decision.symbol, side=decision.side, qty=1, order_type="market")

            status = "[SUCCESS] : 주문 성공" if result.ok else f"[FAIL] : 주문 실패 {result.message}"
            print(f"[{symbol}] {decision.side} (RSI={decision.rsi:.2f}) {status}")

    except Exception as e:
        print(f"[ERROR] handle_realtime_price({symbol}) 실패: {e}")