import os, logging, time, redis

from auto_stock.celery import app
from trading.models import OrderRequest
from trading.services.rsi_process import get_rsi_signal
from trading.services.save_order_execution import save_execution_data
from trading.services.calculate_order import calculate_target_price
from kis.websocket.trading_ws import order_buy, order_sell

logger = logging.getLogger(__name__)

tr_id = os.getenv("ORDER_EXECUTION_TR_ID")
## TODO DB에서 직접 불러와 사용하도록 수정
hts_id_key = os.getenv("HTS_ID")
r = redis.Redis(decode_responses=True)

## celery -A auto_stock worker -l info
@app.task
def auto_order(order_id):
    order = OrderRequest.objects.get(id=order_id)
    # 상태 변경
    order.status = "BUY_PENDING"
    order.save()

    # 1. RSI 신호 검사
    if not check_buy_signal(order):
        return

    # 2. 매수 요청
    buy_result = order_buy(order.symbol, qty=order.quantity, order_type="market")

    # 2-1. 매수 요청 실패
    if not buy_result.ok:
        order.status = "BUY_REQUEST_FAILED"
        order.save()
        return

    # 매수 성공: 체결 정보 저장
    time.sleep(1.2)
    # 매수 체결 정보 조회
    exec_data = save_execution_data(order, buy_result, "BUY")

    # 3. 매도 목표가 계산
    target_price = calculate_target_price(exec_data.executed_price, order.target_profit)

    order.status = "SELL_PENDING"
    order.target_price = target_price
    order.save()

    # 4. 매도 주문
    time.sleep(1.2)
    sell_result = order_sell(order.symbol, order.quantity, target_price,"limit")

    ## 매도 요청 실패
    if not sell_result.ok:
        order.status = "SELL_REQUEST_FAILED"
        order.save()
        return

    ## 체결 정보
    order.kis_order_id = sell_result.order_id
    order.save()

    # 매도 체결 정보 조회
    save_execution_data(order, buy_result, "SELL")


## 매수 시그널 검사
def check_buy_signal(order: OrderRequest) -> bool:
    signal, rsi = get_rsi_signal(order.symbol, 20, order.risk)
    if signal != "BUY":
        order.message = f"매수 신호 없음 (RSI={rsi})"
        order.save()
        logger.info("[AUTO-BUY] 매수 신호 없음")
        return False
    return True