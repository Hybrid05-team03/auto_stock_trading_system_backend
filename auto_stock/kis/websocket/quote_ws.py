import os
import logging

from websocket import create_connection
from typing import Optional, Dict, Any

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.util.handler_ws import _send_subscription, _wait_for_trade_frame

logger = logging.getLogger(__name__)

# web socket
WS_BASE_URL = os.getenv("KIS_WS_BASE_URL")
WS_CONNECT_TIMEOUT = float(os.getenv("INDICES_WS_CONNECT_TIMEOUT"))
REALTIME_TR_ID = os.getenv("KIS_REALTIME_TR_ID")
WS_CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE")

# --------------------------------------------------------------------
# 실시간 시세 조회 (WebSocket)
# --------------------------------------------------------------------
def fetch_realtime_quote(tr_id: str, symbol: str) -> Optional[Dict[str, Any]]:
    approval_key = get_web_socket_key()
    ws = create_connection(WS_BASE_URL, timeout=WS_CONNECT_TIMEOUT)

    try:
       
        # 연결 후 Subscription 메시지 보내기
        _send_subscription(ws, approval_key=approval_key,
                           tr_id=REALTIME_TR_ID, code=symbol, tr_type="1")

        result = _wait_for_trade_frame(ws, symbol, REALTIME_TR_ID)
        _send_subscription(ws, approval_key, REALTIME_TR_ID, symbol, tr_type="2")

        ws.close()

        if result:
            logger.info(f"[WS] {symbol}: {result['price']} @ {result['timestamp']}")
        return result

    except Exception as e:
        logger.error(f"[WS ERROR] {symbol}: {e}")
        return None