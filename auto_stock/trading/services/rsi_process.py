from kis.api.price import fetch_price_series


## RSI 지표 계산
def get_rsi(symbol: str, period: int = 14):
    series = fetch_price_series(symbol)
    closes = [row["close"] for row in series]
    return calculate_rsi(closes, period)


def calculate_rsi(prices, period: int = 14):
    if len(prices) < period + 1:
        return None

    import pandas as pd

    series = pd.Series(prices)
    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain.iloc[-1] / avg_loss.iloc[-1] if avg_loss.iloc[-1] != 0 else float("inf")
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi), 2)


## RSI 지표 계산
def get_rsi(symbol: str, period: int = 14):
    series = fetch_price_series(symbol)
    closes = [row["close"] for row in series]
    return calculate_rsi(closes, period)


def calculate_rsi(prices, period: int = 14):
    if len(prices) < period + 1:
        return None

    import pandas as pd

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
def get_rsi_signal(symbol: str, period: int = 14):
    prices = fetch_price_series(symbol)

    if not prices:
        return None, None

    closes = [row["close"] for row in prices]
    rsi = calculate_rsi(closes, period=period)

    if rsi is None:
        return None, None

    if rsi < 40:
        return "BUY", rsi
    elif rsi > 60:
        return "SELL", rsi
    else:
        return None, rsi