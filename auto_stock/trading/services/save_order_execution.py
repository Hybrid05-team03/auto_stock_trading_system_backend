import time, logging
from datetime import datetime

from trading.data.trading_result import TradeResult
from trading.models import OrderRequest, OrderExecution

from kis.api.account import fetch_recent_ccld

logger = logging.getLogger(__name__)


## 체결 데이터 저장
def save_execution_data(order: OrderRequest, executed_result: TradeResult, side: str):

    # --- side 기반 상태 매핑 ---
    pending_status = "BUY_PENDING" if side == "BUY" else "SELL_PENDING"
    done_status = "BUY_DONE" if side == "BUY" else "SELL_DONE"
    dvsd_code = "01" if side == "SELL" else "02" # 01(매도) 02(매수)

    interval = 2   # 2초 간격

    exec_data = fetch_recent_ccld(executed_result.order_id, executed_result.symbol, dvsd_code)

    while exec_data is None :
        time.sleep(interval)
        exec_data = fetch_recent_ccld(executed_result.order_id, executed_result.symbol, dvsd_code)

        ## 체결 데이터 조회 성공
        if (exec_data):
            logger.info(f"[INFO] 체결 데이터 조회={exec_data}")
            break

    if not exec_data:
        logger.warning("[WARN] 체결 정보 없음 (timeout)")
        order.status = pending_status
        return None

    # 리스트로 오는 경우 첫 데이터만 사용
    if isinstance(exec_data, list):
        exec_data = exec_data[0]

    order.status = done_status
    executed_at = datetime.strptime(exec_data["date"] + exec_data["time"].zfill(6),
                                    "%Y%m%d%H%M%S")

    order.save()
    return OrderExecution.objects.create(
        order_request=order,
        kis_order_id=executed_result.order_id,
        kis_message=executed_result.message,
        executed_side=side,
        executed_price=exec_data["price"],
        executed_quantity=exec_data["qty"],
        executed_at=executed_at,
    )