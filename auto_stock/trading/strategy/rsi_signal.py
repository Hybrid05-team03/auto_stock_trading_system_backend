from trading.services.rsi_calculator import get_rsi_for_symbol

def get_trade_signal(symbol: str, period: int = 2) -> dict:
    df = get_rsi_for_symbol(symbol, period)
    if df.empty:
        return {"symbol": symbol, "action": "HOLD", "reason": "데이터 없음"}

    latest = df.iloc[-1]
    rsi = latest["RSI"]
    price = latest["close"]

    if rsi < 30:
        return {"symbol": symbol, "action": "BUY", "rsi": rsi, "price": price, "reason": "RSI 과매도"}
    elif rsi > 70:
        return {"symbol": symbol, "action": "SELL", "rsi": rsi, "price": price, "reason": "RSI 과매수"}
    else:
        return {"symbol": symbol, "action": "HOLD", "rsi": rsi, "price": price, "reason": "보합 구간"}