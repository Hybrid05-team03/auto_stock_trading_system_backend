import logging, time, redis

from auto_stock.celery import app
from trading.models import OrderRequest
from trading.services.rsi_process import get_rsi_signal
from kis.websocket.trading_ws import order_sell

logger = logging.getLogger(__name__)

r = redis.Redis(decode_responses=True)


# celery 비트로 주기적 비동기 실행
## celery -A auto_stock beat -l info
@app.task(bind=True, max_retries=None)
def auto_sell(self, order_id):
    order = OrderRequest.objects.get(id=order_id)
    buy_exec = order.orderexecution_set.get(side="BUY")

    buy_price = buy_exec.executed_price
    qty = buy_exec.executed_qty
    symbol = order.symbol

    while True:
        # 1) 실시간 가격 가져오기 (Redis → WS 구조 지원)
        current_price = r.get("price:"+symbol)
        if not current_price:
            time.sleep(1)
            continue

        # 2) 목표 수익률 도달 여부
        profit_rate = (current_price - buy_price) / buy_price * 100
        if order.target_profit and profit_rate >= order.target_profit:
            result = order_sell(symbol, qty, order_type="market")
            logger.info(f"[SELL-MONITOR] 목표 수익률 도달 → 매도 실행: {result.message}")
            return

        # 3) RSI 기반 매도 신호
        signal, rsi = get_rsi_signal(symbol, 14, order.risk)
        if signal == "SELL":
            result = order_sell(symbol, qty, order_type="market")
            logger.info(f"[SELL-MONITOR] RSI SELL 신호 → 매도 실행: {result.message}")
            return

        # 다음 체크까지 대기
        time.sleep(1)