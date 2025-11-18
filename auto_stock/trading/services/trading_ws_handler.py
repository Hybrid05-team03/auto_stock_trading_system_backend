# trading/services/realtime_handler.py

import logging
from trading.services.trading_auto import auto_trade

logger = logging.getLogger(__name__)

def realtime_price_callback(event: dict):

    symbol = event["symbol"]
    price = event["price"]

    logger.info(f"[Realtime] {symbol}: {price}")

    # 여기서 자동매매 전략 실행
    auto_trade(symbol, price)