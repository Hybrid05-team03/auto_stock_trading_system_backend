import pandas as pd
from kis.api.price import fetch_price_series


def calculate_rsi(prices, period: int = 14):
    if len(prices) < period + 1:
        return None

    series = pd.Series(prices)
    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain.iloc[-1] / avg_loss.iloc[-1] if avg_loss.iloc[-1] != 0 else float("inf")
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi), 2)


## 계산 후 매매 신호 생성
def get_rsi_signal(symbol: str, period: int, risk: str):
    VALID_RISK = {"low", "mid", "high"}

    if risk not in VALID_RISK:
        raise ValueError(f"Invalid risk value: {risk}")

    thresholds = {
        "low": 60,
        "mid": 35,
        "high": 30,
    }
    buy_thr = thresholds[risk]
    prices = fetch_price_series(symbol)

    if not prices:
        return None, None

    closes = [row["close"] for row in prices]
    rsi = calculate_rsi(closes, period=period)

    if rsi is None:
        return None, None

    return ("BUY", rsi) if rsi < buy_thr else (None, rsi)