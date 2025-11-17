import pandas as pd
from datetime import datetime

from kis.api.quote import kis_get_last_quote
from kis.websocket.price_ws import start_price_stream
from trading.services.trading_rsi_calculate import calculate_rsi
from trading.services.trading_strategy import determine_signal
from kis.websocket.trading_ws import KISTRADING


df_cache = {}
trader = KISTRADING(dry_run=False)

def on_price_update(symbol, price):
    global df_cache

    df = df_cache.get(symbol)
    df = pd.concat([df, pd.DataFrame([{
        "date": datetime.now(),
        "close": price
    }])], ignore_index=True).tail(100)

    rsi_series = calculate_rsi(df, period=2).fillna(50)
    rsi = float(rsi_series.iloc[-1])

    signal = determine_signal(symbol, rsi, price)
    print(f"[{symbol}] {signal.side} | Price={price} | {signal.reason}")

    if signal.side in ["BUY", "SELL"]:
        trader.place_order(symbol, signal.side, qty=1, order_type="market")

    df_cache[symbol] = df


def auto_trade(symbol: str):
    df_cache[symbol] = kis_get_last_quote(symbol, count=100)
    start_price_stream(symbol, on_price_update)