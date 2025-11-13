import logging

from celery import shared_task
from trading.services.rsi_decision import auto_trade

# 로거 설정
logger = logging.getLogger(__name__)

# 주문 처리 로직 비동기 실행
@shared_task(name="trading.run_auto_trading")
def run_auto_trading(symbol: str):
    try:
        logger.info(f"[{symbol}] 자동매매 태스크를 시작합니다.")
        auto_trade(symbol)
    except Exception as e:
        logger.error(f"[{symbol}] 자동매매 태스크 실행 중 오류 발생: {e}", exc_info=True)