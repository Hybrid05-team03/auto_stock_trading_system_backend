import os
import json
import redis
import logging

from websocket import create_connection
from typing import Optional, Dict, Any

from kis.auth.kis_ws_key import get_web_socket_key
from kis.websocket.util.handler_ws import _send_subscription, _wait_for_trade_frame


# 환경 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WS_BASE_URL = os.getenv("KIS_WS_BASE_URL")
WS_CONNECT_TIMEOUT = float(os.getenv("INDICES_WS_CONNECT_TIMEOUT", 10))
REALTIME_TR_ID = os.getenv("KIS_REALTIME_TR_ID", "H0STASP0")
WS_CUST_TYPE = os.getenv("KIS_WS_CUSTOMER_TYPE", "P")
TR_KEY = os.getenv("KIS_TR_KEY", "005930")  # 기본: 삼성전자

REDIS_CHANNEL = "kis.quote"

logger = logging.getLogger(__name__)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# --------------------------------------------------------------------
# 실시간 호가 조회 (WebSocket)
# --------------------------------------------------------------------
def start_quote_streaming(symbol: str = TR_KEY, tr_id: str = REALTIME_TR_ID):
    try:
        approval_key = get_web_socket_key()
        print("키는: ", approval_key)
        ws = create_connection(WS_BASE_URL, timeout=WS_CONNECT_TIMEOUT)

        logger.info(f"[WS] 연결됨: {symbol}, tr_id={tr_id}")
        _send_subscription(ws, approval_key, tr_id, symbol, "1")  # 구독 시작

        while True:
            result = _wait_for_trade_frame(ws, symbol, tr_id)
            if result:
                redis_data = {
                    "symbol": symbol,
                    "price": result.get("price"),
                    "timestamp": result.get("timestamp"),
                    "raw": result
                }
                r.publish(REDIS_CHANNEL, json.dumps(redis_data))
                logger.info(f"[QUOTE] {symbol}: {result.get('price')}")

    except Exception as e:
        logger.error(f"[WS ERROR] {symbol}: {e}")
    finally:
        try:
            _send_subscription(ws, approval_key, tr_id, symbol, "2")  # 구독 해제
            ws.close()
        except:
            pass
        logger.info("[WS] 연결 종료됨")


# --------------------------------------------------------------------
# 단건 조회 (디버그용)
# --------------------------------------------------------------------
def fetch_realtime_quote(endpoint: str, symbol: str, tr_id: str) -> Optional[Dict[str, Any]]:
    approval_key = get_web_socket_key()
    ws = create_connection(WS_BASE_URL + endpoint, timeout=WS_CONNECT_TIMEOUT)

    try:
        _send_subscription(ws, approval_key, tr_id, symbol, "1")
        result = _wait_for_trade_frame(ws, symbol, tr_id)
        _send_subscription(ws, approval_key, tr_id, symbol, "2")
        ws.close()

        if result:
            logger.info(f"[WS:1회] {symbol}: {result['price']} @ {result['timestamp']}")
        return result

    except Exception as e:
        logger.error(f"[WS ERROR] {symbol}: {e}")
        return None