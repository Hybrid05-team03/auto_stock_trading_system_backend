import time, logging
from datetime import datetime

from trading.data.trading_result import TradeResult
from trading.models import OrderRequest, OrderExecution

from kis.api.account import fetch_recent_ccld

logger = logging.getLogger(__name__)


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