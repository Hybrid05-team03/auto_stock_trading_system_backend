import logging, time
from datetime import datetime
from auto_stock.celery import app
from trading.data.trading_result import TradeResult
from trading.models import OrderRequest, OrderExecution
from trading.services.rsi_process import get_rsi_signal
from kis.websocket.trading_ws import order_buy, order_sell
from kis.api.account import fetch_recent_ccld, fetch_unfilled_status

logger = logging.getLogger(__name__)


## celery -A auto_stock worker -l info
@app.task
def auto_buy(order_id):
    order = OrderRequest.objects.get(id=order_id)
    # 상태 변경
    order.status = "BUY_PENDING"
    order.save()

    # RSI 계산
    signal, rsi = get_rsi_signal(order.symbol, 20, order.risk)
    if signal != "BUY":
        order.status = "BUY_REQUEST_FAILED"
        order.message = f"매수 신호 없음 (RSI={rsi})"
        order.save()
        logger.info("[AUTO-BUY] 매수 신호 없음")
        return

    # 매수 요청
    buy_result = order_buy(order.symbol, qty=order.quantity, order_type="market")
    if buy_result.ok:
        order.status = "BUY_DONE"
        order.message = buy_result.message
        logger.info("[AUTO-BUY] 매수 처리 완료")
        order.save()

        # 매수 체결 정보 저장
        time.sleep(1.2)
        exec_data = save_execution_data(order, buy_result, "BUY")

        # logger.info(f"[DEBUG] 데이터 확인 {buy_result.price} {exec_data.executed_price}")
        # 매도 목표가 계산
        if order.target_profit == 0:
            target_price = exec_data.executed_price
        else:
            raw_price = exec_data.executed_price * (1 + order.target_profit / 100)
            target_price = normalize_price(int(raw_price))
        order.target_price = target_price
        order.save()

        # 매도 주문
        time.sleep(1.2) # 요청 횟수 제한 방지
        sell_result = order_sell(order.symbol, order.quantity, target_price, "limit")

        ## 매도 요청 완료
        if sell_result.ok:
            order.sell_order_id = sell_result.order_id  # 매도 주문번호
            order.status = "SELL_DONE"
            logger.info("[AUTO-SELL] 매도 요청 완료")
            save_execution_data(order, sell_result, "SELL")
        else:
            order.status = "SELL_REQUEST_FAILED"
            order.message = sell_result.message
            logger.info("[AUTO-SELL] 매도 요청 실패")
        order.save()


def get_tick(price: int) -> int:
    if price < 2000:
        return 1
    elif price < 5000:
        return 5
    elif price < 10000:
        return 10
    elif price < 50000:
        return 50
    elif price < 100000:
        return 100
    elif price < 500000:
        return 500
    else:
        return 1000


## 매도 목표가 반올림 처리
def normalize_price(price: int) -> int:
    tick = get_tick(price)
    return (price // tick) * tick


## 미체결 매도건 조회 후 재주문
@app.task
def retry_unfilled_sells():
    # 미체결 매도건 조회
    orders = (
        OrderRequest.objects
        .filter(status="SELL_PENDING")
    )

    for order in orders:
        status = fetch_unfilled_status(order.sell_order_id, order.symbol)
        if not status:
            continue

        pending = status["remaining_qty"]
        # 전체 체결
        if pending == 0:
            logger.info("[SELL-DONE] 매수 완료")
            # 매도 체결 정보 조회 및 저장
            sell_exec_result = TradeResult(
                ok=True,
                order_id=order.sell_order_id,
                symbol=order.symbol,
                message="SELL Filled"
            )
            save_execution_data(order, sell_exec_result, "SELL")
            order.status = "SELL_DONE"
            order.save()
            continue

        # 재주문
        if not cancel_kis_order(order.sell_order_id):
            continue

        new_result = order_sell(
            symbol=order.symbol,
            qty=pending,
            price=order.target_price,
            order_type="limit",
        )

        if new_result.ok:
            order.sell_order_id = new_result.order_id
            order.save()
        else:
            logger.warning(f"[SELL-RETRY] 재주문 실패: {new_result.message}")


## 체결 데이터 저장 함수
def save_execution_data(order: OrderRequest, executed_result: TradeResult, side: str):

    time.sleep(2)
    exec_data = fetch_recent_ccld(executed_result.order_id, executed_result.symbol)

    ## 아직 체결되기 전인 경우
    if not exec_data:
        logger.warning("[WARN] 체결 정보 없음")
        return None

    # 리스트로 오는 경우 첫 데이터만 사용
    if isinstance(exec_data, list):
        exec_data = exec_data[0]

    executed_at = datetime.strptime(exec_data["date"] + exec_data["time"].zfill(6),
                                    "%Y%m%d%H%M%S")

    return OrderExecution.objects.create(
        order_request=order,
        kis_order_id=executed_result.order_id,
        kis_message=executed_result.message,
        executed_side=side,
        executed_price=exec_data["price"],
        executed_quantity=exec_data["qty"],
        executed_at=executed_at,
    )


## 주문 취소 함수
def cancel_kis_order(order_id: str):
    # TODO 주문 취소 로직 추가
    return ""