import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import time

from websocket import WebSocketTimeoutException, WebSocketConnectionClosedException

WS_CONNECT_TIMEOUT = float(os.getenv("INDICES_WS_CONNECT_TIMEOUT"))
WS_MESSAGE_TIMEOUT = float(os.getenv("INDICES_WS_MESSAGE_TIMEOUT"))
WS_CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE")
KST = timezone(timedelta(hours=9))

# --------------------------------------------------------------------
# WebSocket 메시지 송수신
# --------------------------------------------------------------------
def _send_subscription(ws, approval_key: str, tr_id: str, code: str, tr_type: str):

    message = {
        "header": {
            "approval_key": approval_key,
            "custtype": WS_CUST_TYPE,
            "tr_type": tr_type,
            "content-type": "utf-8",
        },
        "body": {
            "input": {"tr_id": tr_id, "tr_key": code}
        },
    }
    ws.send(json.dumps(message))


# --------------------------------------------------------------------
# WebSocket 데이터 파싱
# --------------------------------------------------------------------
def _parse_event_payload(raw: str, expected_tr_id: str, code: str) -> Optional[Dict[str, Any]]:
    try:
        _, tr_id, _, body = raw.split("|", 3)
    except ValueError:
        return None
    if tr_id != expected_tr_id:
        return None

    parts = body.split("^")
    if len(parts) < 3 or parts[0] != code:
        return None

    # float 변환 (유틸 삭제 → 인라인 처리)
    try:
        price = float(parts[2])
    except (ValueError, TypeError):
        return None

    # 타임스탬프 처리 (유틸 삭제 → 인라인 처리)
    try:
        date_str = parts[33] if len(parts) > 33 else ""
        time_str = parts[1] if len(parts) > 1 else ""
        base = datetime.strptime(f"{date_str}{time_str[:6]}", "%Y%m%d%H%M%S")
        timestamp = base.replace(tzinfo=KST).isoformat()
    except Exception:
        timestamp = datetime.now(KST).isoformat()

    return {"price": price, "timestamp": timestamp}

def _wait_for_trade_frame(ws, code: str, tr_id: str) -> Optional[Dict[str, Any]]:
    deadline = time.time() + WS_MESSAGE_TIMEOUT
    while time.time() < deadline:
        try:
            ws.settimeout(max(deadline - time.time(), 0.1))
            raw = ws.recv()
        except (WebSocketTimeoutException, WebSocketConnectionClosedException):
            return None

        if not raw:
            continue
        if raw[0] in ("0", "1") and "|" in raw:
            event = _parse_event_payload(raw, tr_id, code)
            if event:
                return event
    return None