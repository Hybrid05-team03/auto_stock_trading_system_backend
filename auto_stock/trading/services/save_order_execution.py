import time, logging
from datetime import datetime

from trading.data.trading_result import TradeResult
from trading.models import OrderRequest, OrderExecution

from kis.api.account import fetch_recent_ccld

logger = logging.getLogger(__name__)


## 체결 데이터 저장 함수
def save_execution_data(order: OrderRequest, executed_result: TradeResult, side: str):

    max_wait = 60  # 최대 20초 동안 반복 조회
    interval = 2   # 2초 간격

    for _ in range(max_wait // interval):
        time.sleep(interval)
        exec_data = fetch_recent_ccld(executed_result.order_id, executed_result.symbol)

        ## 체결 데이터 조회 성공
        if exec_data:
            logger.warning("[WARN] 체결 정보 조회 완료")
            break

    if not exec_data:
        logger.warning("[WARN] 체결 정보 없음 (timeout)")
        return None

    # 리스트로 오는 경우 첫 데이터만 사용
    if isinstance(exec_data, list):
        exec_data = exec_data[0]

    order.status = "SELL_DONE"
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


## 매도 체결 정보 저장
def save_execution_data_sell(order: OrderRequest, executed_result: TradeResult):
    return OrderExecution.objects.create(
        order_request=order,
        kis_order_id=executed_result.order_id,
        kis_message=executed_result.message,
        executed_side="SELL",
        executed_price=order.target_price,
        executed_quantity=order.quantity,
        # executed_at=executed_at,
    )
