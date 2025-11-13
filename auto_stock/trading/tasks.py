# trading/tasks.py

import logging
from celery import shared_task
from trading.services.trading_auto import auto_trade

logger = logging.getLogger(__name__)

@shared_task(name="trading.run_auto_trading")
def run_auto_trading(symbol: str):
    logger.info(f"[AUTO-TRADE] {symbol} 자동매매 태스크 시작")

    try:
        auto_trade(symbol)
    except Exception as e:
        logger.error(
            f"[AUTO-TRADE] {symbol} 자동매매 실행 중 오류 발생: {e}",
            exc_info=True
        )