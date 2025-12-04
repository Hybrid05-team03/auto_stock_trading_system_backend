import logging, time

from auto_stock.celery import app
from trading.models import OrderRequest
from trading.services.rsi_process import get_rsi_signal
from trading.services.save_order_execution import save_execution_data

from kis.websocket.trading_ws import order_buy, order_sell

logger = logging.getLogger(__name__)


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
    buy_result = request_buy(order)

    # 2-1. 매수 요청 실패
    if not buy_result.ok:
        order.status = "BUY_REQUEST_FAILED"
        order.save()
        return

    # 2-2. 매수 요청 성공 -> 체결 정보 저장
    exec_data = save_execution_data(order, buy_result, "BUY")

    # 2-3. 매수 정보 저장
    order.status = "BUY_DONE"
    order.message = buy_result.message
    order.kis_order_id = buy_result.order_id
    order.save()

    # 3. 매도 목표가 계산
    target_price = calculate_target_price(exec_data.executed_price, order.target_profit)
    order.status = "SELL_PENDING"
    order.target_price = target_price
    order.save()

    # 4. 매도 주문
    sell_result = request_sell(order, target_price)

    if sell_result.ok:
        order.sell_order_id = sell_result.order_id
        order.status = "SELL_DONE"
        handle_sell_execution(order, sell_result)
    else:
        order.status = "SELL_REQUEST_FAILED"
        order.message = sell_result.message
    order.save()


## 매수 시그널 검사
def check_buy_signal(order: OrderRequest) -> bool:
    signal, rsi = get_rsi_signal(order.symbol, 20, order.risk)
    if signal != "BUY":
        order.status = "BUY_REQUEST_FAILED"
        order.message = f"매수 신호 없음 (RSI={rsi})"
        order.save()
        logger.info("[AUTO-BUY] 매수 신호 없음")
        return False
    return True


## 매수 요청
def request_buy(order: OrderRequest):
    return order_buy(order.symbol, qty=order.quantity, order_type="market")


## 매수 체결 데이터 저장
def handle_buy_execution(order: OrderRequest, buy_result):
    time.sleep(1.2)
    exec_data = save_execution_data(order, buy_result, "BUY")
    return exec_data


def get_tick(price: int) -> int:
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 10000: return 10
    elif price < 50000: return 50
    elif price < 100000: return 100
    elif price < 500000: return 500
    else: return 1000


## 매도 목표가 반올림 처리
def normalize_price(price: int) -> int:
    tick = get_tick(price)
    return (price // tick) * tick


## 매도 목표가 계산
def calculate_target_price(exec_price: int, target_profit: int) -> int:
    if target_profit == 0:
        return exec_price

    raw_price = exec_price * (1 + target_profit / 100)
    return normalize_price(int(raw_price))


## 매도 주문 요청
def request_sell(order: OrderRequest, target_price: int):
    time.sleep(1.2)
    return order_sell(
        order.symbol,
        order.quantity,
        target_price,
        "limit"
    )


## 매도 체결 데이터 처리
def handle_sell_execution(order: OrderRequest, sell_result):
    logger.info("[AUTO-SELL] 매도 요청 완료")
    save_execution_data(order, sell_result, "SELL")