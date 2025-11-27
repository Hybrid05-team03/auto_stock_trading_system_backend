import logging

from auto_stock.celery import app
from trading.models import OrderRequest
from trading.services.rsi_process import get_rsi_signal
from kis.websocket.trading_ws import order_buy

logger = logging.getLogger(__name__)


# celery 워커로 비동기 실행
## celery -A auto_stock worker -l info
@app.task
def auto_buy(order_id):
    order = OrderRequest.objects.get(id=order_id)

    # 상태 변경
    order.status = "PROCESSING"
    order.save()

    # RSI 계산
    signal, rsi = get_rsi_signal(order.symbol, period=20)
    print(f"auto buy 디버깅 {signal, rsi}")
    if signal != "BUY":
        order.status = "FAIL"
        order.message = f"매수 신호 없음 (RSI={rsi})"
        order.save()
        logger.info("[AUTO-BUY] 매수 신호 없음")
        return

    # 시장가 매수
    result = order_buy(order.symbol, qty=order.quantity, order_type="market")

    # DB 저장
    if result.ok:
        order.status = "SUCCESS"
        logger.info("[AUTO-BUY] 시장가 매수 성공")
    else:
        order.status = "FAIL"
        logger.info("[AUTO-BUY] 시장가 매수 실패")
    order.message = result.message
    order.save()