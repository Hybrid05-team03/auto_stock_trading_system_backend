import logging, time
from auto_stock.celery import app
from trading.data.trading_result import TradeResult
from trading.models import OrderRequest
from kis.websocket.trading_ws import order_buy, order_sell, order_cancel
from kis.api.account import fetch_recent_ccld, fetch_unfilled_status
from trading.services.save_order_execution import save_execution_data

logger = logging.getLogger(__name__)


## 미체결 매수건 조회 후 재주문


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
        if not cancel_kis_order(order.symbol, order.sell_order_id):
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


## 주문 취소 함수
def cancel_kis_order(symbol: str, order_id: str):
    order_cancel(symbol, order_id, 0, True)
    return ""