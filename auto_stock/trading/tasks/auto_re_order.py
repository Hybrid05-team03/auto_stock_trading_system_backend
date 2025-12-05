import logging, time
from django.utils import timezone
from celery import chain

from auto_stock.celery import app
from trading.models import OrderRequest, OrderExecution
from kis.websocket.trading_ws import order_sell, order_cancel
from trading.tasks.auto_order import auto_order
from trading.services.save_order_execution import save_execution_data_sell
from trading.services.calculate_order import calculate_target_price

logger = logging.getLogger(__name__)


## 매도 후 매수 연쇄 실행 (KIS 거래 건수 제한 방지)
@app.task
def retry_unfilled_sells_chain():
    return chain(
        retry_unfilled_sells.s(), # 매도
        delay_task.si(5),
        retry_unfilled_buys.si() # 매수
    )()


## celery worker 블로킹 방지 함수
@app.task
def delay_task(seconds):
    time.sleep(seconds)
    return True


## 미체결 매수건 조회 후 재주문
@app.task
def retry_unfilled_buys():
    orders = OrderRequest.objects.filter(
        status__in=["BUY_PENDING", "BUY_REQUEST_FAILED"]
    )
    today = timezone.now().date()

    for order in orders:
        # 기존 주문이 과거 것이라면 취소
        old_exec = (
            OrderExecution.objects.filter(
                order_request=order,
                executed_side="BUY",
                executed_at__date__lt=today,
            )
            .order_by("-executed_at")
            .first()
        )

        if old_exec:
            order_cancel(symbol=order.symbol, order_id=old_exec.kis_order_id)

        # 매수 → 매도까지 전체 프로세스 재실행
        auto_order.delay(order.id)


## 미체결 매도건 조회 후 재주문
@app.task
def retry_unfilled_sells():
    # 미체결 매도건 DB 조회
    orders = (OrderRequest.objects.filter(status__in=["BUY_DONE", "SELL_PENDING", "SELL_REQUEST_FAILED"]))
    today = timezone.now().date()

    for order in orders:
        # 체결 정보 조회
        order_execution = (OrderExecution.objects.filter(
            order_request=order, executed_side="SELL", executed_at__date__lt=today,
        ).order_by("-executed_at").first())

        ## 기존 매도 체결 정보 있는 경우
        if order_execution is not None:
            # 주문 취소
            order_cancel(symbol=order.symbol, order_id=order_execution.kis_order_id, qty=order.quantity)

        ## 기존 매도 체결 정보 없는 경우
        else:
            logger.warning(f"[WARN] 다시 매도 : 매수 체결 정보 확인 ===== {order.id, order.status}")
            # 매수 체결 정보 조회
            buy_execution = (OrderExecution.objects.filter(
                order_request=order, executed_side="BUY",
            ).order_by("-executed_at").first())
            target_price = calculate_target_price(buy_execution.executed_price, order.target_profit)
            order.target_price = target_price
            order.save()

        # 다시 매도 주문
        sell_result = order_sell(order.symbol, order.quantity, order.target_price, "limit")

        if not sell_result.ok:
            order.status  ="SELL_REQUEST_FAILED"
            order.save()
            return

        ## 매도 체결 정보 저장
        time.sleep(1.2)
        logger.info(f"체결 정보 ========= {sell_result}")
        save_execution_data_sell(order, sell_result)
        ## 매도 정보 저장
        order.status = "SELL_DONE"
        order.save()