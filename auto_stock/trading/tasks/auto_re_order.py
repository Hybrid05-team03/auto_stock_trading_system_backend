import logging, time
from django.utils import timezone
from auto_stock.celery import app
from trading.models import OrderRequest, OrderExecution
from kis.websocket.trading_ws import order_sell, order_cancel
from trading.tasks.auto_order import auto_order
from trading.services.save_order_execution import save_execution_data

logger = logging.getLogger(__name__)


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
    orders = (OrderRequest.objects.filter(status="SELL_PENDING"))
    today = timezone.now().date()

    for order in orders:
        # 체결 정보 조회
        order_execution = (OrderExecution.objects.filter(
            order_request=order, executed_side="SELL", executed_at__date__lt=today,
        ).order_by("-executed_at").first())

        # 주문 취소
        if order_execution != None:
            logger.info("NONE아니다-----------")
            order_cancel(symbol=order.symbol, order_id=order_execution.kis_order_id, qty=order.quantity)

        # 다시 매도 주문
        sell_result = order_sell(order.symbol, order.quantity, order.target_price, "limit")

        if not sell_result.ok:
            order.status  ="SELL_REQUEST_FAILED"
            order.save()
            return

        ## 매도 체결 정보 저장
        time.sleep(1.2)
        save_execution_data(order, sell_result, "SELL")

        ## 매도 정보 저장
        order.status = "SELL_DONE"
        order.save()