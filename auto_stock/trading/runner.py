import time
from datetime import datetime
import numpy as np
from trading.services.rsi_calculator import calculate_rsi
from trading.broker.kis_order import place_order
from kis.api.quote import get_daily_price


def get_recent_prices(symbol: str, count: int = 100):
    """최근 종가 데이터 100개 가져오기"""
    df = get_daily_price(symbol, count=count)
    if df.empty:
        raise ValueError(f"가격 데이터를 불러올 수 없습니다. symbol={symbol}")
    return df[["date", "close"]]


def get_latest_price(symbol: str):
    """가장 최근 체결가 조회 (실제로는 WebSocket 이벤트로 대체 가능)"""
    df = get_daily_price(symbol, count=1)
    return float(df["close"].iloc[-1])


def auto_trading_runner(symbol: str):
    print(f"🔄 [{symbol}] 자동매매 시작")

    df = get_recent_prices(symbol, count=100)

    while True:
        latest_price = get_latest_price(symbol)

        if latest_price is None or np.isnan(latest_price):
            print(f"[{symbol}] ❌ 가격 데이터 없음, 다음 루프로 넘어감")
            time.sleep(5)
            continue

        df.loc[len(df)] = {"date": datetime.now(), "close": latest_price}
        df = df.tail(100)

        # 최소 2개 이상 데이터 있을 때만 RSI 계산
        if len(df) < 2:
            print(f"[{symbol}] 데이터 부족 (len={len(df)})")
            time.sleep(5)
            continue

        rsi_series = calculate_rsi(df, period=2)
        if rsi_series.isna().all():
            print(f"[{symbol}] RSI 계산 불가 (NaN)")
            time.sleep(5)
            continue

        rsi = rsi_series.iloc[-1]
        print(f"[{symbol}] RSI={rsi:.2f}, Price={latest_price}")

        if rsi < 5:
            place_order(symbol, action="BUY", price=latest_price)
        elif rsi > 80:
            place_order(symbol, action="SELL", price=latest_price)

        time.sleep(5)