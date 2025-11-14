from trading.data.trading_data import TradeSignalParam

def determine_signal(symbol: str, rsi: float, price: float):
    if rsi < 5:
        return TradeSignalParam(symbol, "BUY", f"RSI={rsi:.2f}", rsi, price)
    elif rsi > 80:
        return TradeSignalParam(symbol, "SELL", f"RSI={rsi:.2f}", rsi, price)
    else:
        return TradeSignalParam(symbol, "HOLD", f"RSI={rsi:.2f}", rsi, price)