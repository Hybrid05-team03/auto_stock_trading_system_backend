import os
import json
import websocket
import threading

from kis.auth.kis_ws_key import get_web_socket_key

WS_URL = os.getenv("KIS_WS_BASE_URL")
TR_ID = "H0STCNT0"  # 국내 주식 실시간 체결가
CUSTTYPE = os.getenv("KIS_WS_CUSTOMER_TYPE")
approval_key = get_web_socket_key()


def build_subscribe_msg(symbol: str):
    return {
        "header": {
            "approval_key": approval_key,
            "custtype": CUSTTYPE,
            "tr_type": "1",
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": TR_ID,
                "tr_key": symbol,
            }
        },
    }


def parse_tick(raw: str, expected_symbol: str):
    """
    실시간 시세(H0STCNT0) 파싱 (텍스트 기반)
    예시: 0|H0STCNT0|001|000660^093001^123000^...
    """
    # JSON이면 패스 (시스템 메세지)
    if raw.startswith("{"):
        return None

    try:
        header, tr_id, _, body = raw.split("|", 3)
    except ValueError:
        return None

    if tr_id != TR_ID:
        return None

    fields = body.split("^")

    # 최소 3개 필드는 반드시 있어야 함
    if len(fields) < 3:
        return None

    code = fields[0]
    time_str = fields[1]
    price = fields[2]

    if code != expected_symbol:
        return None

    try:
        return {
            "symbol": code,
            "price": float(price),
            "time": time_str,
        }
    except ValueError:
        return None


def start_price_stream(symbol: str, on_price_callback):
    """
    실시간 WebSocket: 가격 수신 → 콜백 전달
    """

    def on_message(ws, msg):
        print("[RAW]", repr(msg))
        tick = parse_tick(msg, symbol)
        if tick is None:
            return  # heartbeat or other message

        on_price_callback(symbol, tick["price"], tick)

    def on_open(ws):
        ws.send(json.dumps(build_subscribe_msg(symbol)))

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=lambda ws, err: print("[WS ERROR]", err),
        on_close=lambda ws, code, msg: print("[WS CLOSED]")
    )

    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()
    return ws