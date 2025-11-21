import os
import logging

from websocket import create_connection
from typing import Optional, Dict, Any

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.util.handler_ws import _send_subscription, _wait_for_trade_frame
from kis.websocket.util.handler_index import _wait_for_index_frame
from kis.websocket.util.IndexTick import IndexTick
logger = logging.getLogger(__name__)

# web socket
WS_BASE_URL = os.getenv("KIS_WS_BASE_URL")
WS_CONNECT_TIMEOUT = float(os.getenv("INDICES_WS_CONNECT_TIMEOUT"))
REALTIME_TR_ID = os.getenv("KIS_REALTIME_TR_ID")
WS_CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE")


INDEX_REALTIME_TR_ID = os.getenv("KIS_INDEX_WS_TR_ID")

# --------------------------------------------------------------------
# 실시간 시세 조회 (WebSocket)
# --------------------------------------------------------------------
def fetch_realtime_index(endpoint: str, code: str, tr_id: str) -> Optional[IndexTick]:
    approval_key = get_web_socket_key()
    ws = create_connection(WS_BASE_URL + endpoint, timeout=WS_CONNECT_TIMEOUT)

    try:
        # 구독 시작
        _send_subscription(
            ws,
            approval_key=approval_key,
            tr_id=tr_id,
            code=code,
            tr_type="1",
        )

        # 1번은 테스트용으로 버림
        _wait_for_index_frame(ws, code, tr_id)

        # 2번에서 실제 데이터
        tick = _wait_for_index_frame(ws, code, tr_id)  # ⬅️ IndexTick 또는 None

        # 구독 해제
        _send_subscription(ws, approval_key, tr_id, code, tr_type="2")

        ws.close()

        if tick:
            # 여기서 dict처럼 쓰지 말고, 필드로 접근
            logger.info(
                f"[WS] {code}: prpr_nmix={tick.prpr_nmix}, "
                f"prdy_ctrt={tick.prdy_ctrt}, time={tick.bsop_hour}"
            )
        return tick

    except Exception as e:
        logger.error(f"[WS ERROR] {code}: {e}")
        return None