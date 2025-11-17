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
        if len(fields) < 15:
            return None
        

        ### ------------------ 매핑 추가 ----------------- ###

        # --- Body 필드 매핑 ---
        code_raw        = fields[0]
        time_str        = fields[1]
        prpr_str        = fields[2]
        prdy_vrss_sign  = fields[3]
        prdy_vrss_str   = fields[4]
        prdy_ctrt_str   = fields[5]
        acml_tr_pbmn_str= fields[14]
        
        
        # 코드 포맷 보정 (A005930 → 005930)
        code = code_raw[1:] if code_raw.startswith("A") else code_raw
        if code != symbol:
            return None

        def to_float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        def to_int(v):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        price       = to_float(prpr_str)
        change      = to_float(prdy_vrss_str)
        change_rate = to_float(prdy_ctrt_str)
        trade_value = to_int(acml_tr_pbmn_str)

        if price is None:
            return None

        # "112325" → "11:23:25" 정도로 가공 (원하면 ISO로 바꿔도 됨)
        if len(time_str) >= 6:
            hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:6]
            timestamp = f"{hh}:{mm}:{ss}"
        else:
            timestamp = time_str

        return {
            "symbol": code,
            "price": price,
            "change": change,
            "change_sign": prdy_vrss_sign,
            "change_rate": change_rate,
            "trade_value": trade_value,
            "timestamp": timestamp,
            "raw": frame,
        }
    # -----------------------------
    # 2. JSON 포맷 처리
    #    예: {"body": {"output": {...}}}
    # -----------------------------
    frame_stripped = frame.strip()
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