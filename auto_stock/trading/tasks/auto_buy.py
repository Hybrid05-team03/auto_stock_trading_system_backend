import logging, redis, json, os, time
from datetime import datetime
from auto_stock.celery import app
from celery import shared_task
from trading.models import OrderRequest, OrderExecution
from trading.services.rsi_process import get_rsi_signal
from kis.websocket.trading_ws import order_buy
from kis.api.account import fetch_recent_ccld # 최근 체결가 조회

logger = logging.getLogger(__name__)

r = redis.Redis(decode_responses=True)

# celery 워커로 비동기 실행
## celery -A auto_stock worker -l info
@app.task
def auto_buy(order_id):
    order = OrderRequest.objects.get(id=order_id)

    # 상태 변경
    order.status = "BUYING"
    order.save()

    # RSI 계산
    signal, rsi = get_rsi_signal(order.symbol, 20, order.risk)
    if signal != "BUY":
        order.status = "REQUEST_FAILED"
        order.message = f"매수 신호 없음 (RSI={rsi})"
        order.save()
        logger.info("[AUTO-BUY] 매수 신호 없음")
        return

    # 시장가 매수
    result = order_buy(order.symbol, qty=order.quantity, order_type="market")

    # DB 저장
    if result.ok:
        order.status = "DONE"
        order.message = result.message
        order.kis_order_id = result.order_id
        order.save()

        time.sleep(1.2)  # 초당 제한 회피
        try:
            exec_data = fetch_recent_ccld(order.kis_order_id, order.symbol)
            if exec_data:
                executed_at = datetime.strptime(exec_data.get("date") + exec_data.get("time"), "%Y%m%d%H%M%S")
                OrderExecution.objects.create(
                    order_request=order,
                    side="BUY",
                    executed_price=exec_data["price"],
                    executed_qty=exec_data["qty"],
                    executed_at=executed_at
                )
        except Exception as e:
            logger.warning(f"[INLINE] 체결 정보 저장 실패: {e}")

    else:
        order.status = "REQUEST_FAILED"
        order.message = result.message
        logger.info("[AUTO-BUY] 시장가 매수 실패")
        order.save()