import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
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


def _wait_for_trade_frame(ws, symbol: str, expected_tr_id: str, raw_frame: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    KIS WebSocket 프레임 하나를 받아서 현재가/시간만 뽑아주는 공통 파서.

    지원하는 형식:
    1) 텍스트: "0|H0STCNT0|001|005930^095959^72600^..."
    2) JSON:   {"body": {"output": {...}}}
    3) JSON:   {"body": {"output": "005930^095959^72600^..."}}

    - 유효한 체결 프레임이 아니면 None 반환
    - 실시간 가격 프레임이면 {symbol, price, timestamp, raw} 반환
    """
    try:
        # 1) 프레임 읽기
        if raw_frame is None:
            frame = ws.recv()
        else:
            frame = raw_frame

    except (WebSocketTimeoutException, WebSocketConnectionClosedException) as e:
        # 상위에서 재연결 여부 판단
        print(f"[WS] recv error: {e}")
        return None
    except Exception as e:
        print(f"[WS] unknown recv error: {e}")
        return None

    if not frame:
        # 빈 프레임은 그냥 무시
        return None

    # -----------------------------
    # 1. 파이프/캐럿 텍스트 포맷 처리
    #    예: "0|H0STCNT0|001|005930^095959^72600^..."
    # -----------------------------
    # 첫 글자가 숫자이고 '|' 포함이면 텍스트 포맷일 가능성이 높음
    if "|" in frame and frame[0].isdigit():
        try:
            head, trid, cnt, body = frame.split("|", 3)
        except ValueError:
            # 형식 안 맞으면 무시
            return None

        if trid != expected_tr_id:
            return None

        fields = body.split("^")
        if len(fields) < 3:
            return None

        code = fields[0] or symbol
        price_str = fields[2]  # STCK_PRPR 위치 (문서상 인덱스 2)  [oai_citation:3‡위키독스](https://wikidocs.net/250009?utm_source=chatgpt.com)
        time_str = fields[1] if len(fields) > 1 else ""

        try:
            price = float(price_str)
        except (ValueError, TypeError):
            return None

        # 시간은 그대로 넘기거나, KST datetime으로 가공해도 됨
        timestamp = time_str

        return {
            "symbol": code,
            "price": price,
            "timestamp": timestamp,
            "raw": frame,
        }

    frame_stripped = frame.strip()

    # -----------------------------
    # 2. JSON 포맷 처리
    #    예: {"body": {"output": {...}}}
    # -----------------------------
    if frame_stripped.startswith("{"):
        try:
            data = json.loads(frame_stripped)
        except json.JSONDecodeError as e:
            print(f"[WS] JSON decode error: {e} frame={frame_stripped!r}")
            return None

        body = data.get("body") or {}
        output = body.get("output")

        # (1) output이 dict 인 경우: {"stck_prpr": "...", ...}
        if isinstance(output, dict):
            price_str = output.get("stck_prpr")
            if price_str is None:
                return None

            try:
                price = float(price_str)
            except (ValueError, TypeError):
                return None

            code = (
                output.get("mksc_shrn_iscd")
                or output.get("stck_shrn_iscd")
                or symbol
            )
            timestamp = output.get("stck_cntg_hour") or datetime.now(KST).isoformat()

            return {
                "symbol": code,
                "price": price,
                "timestamp": timestamp,
                "raw": data,
            }

        # (2) output이 문자열인 경우: "005930^095959^72600^..."
        if isinstance(output, str):
            fields = output.split("^")
            if len(fields) < 3:
                return None
            code = fields[0] or symbol
            price_str = fields[2]
            time_str = fields[1] if len(fields) > 1 else ""

            try:
                price = float(price_str)
            except (ValueError, TypeError):
                return None

            return {
                "symbol": code,
                "price": price,
                "timestamp": time_str,
                "raw": data,
            }

        # 그 외 (output 없음/형식 이상) → 무시
        return None

    # -----------------------------
    # 3. 그 외 포맷 (heartbeat 등) → 무시
    # -----------------------------
    return None