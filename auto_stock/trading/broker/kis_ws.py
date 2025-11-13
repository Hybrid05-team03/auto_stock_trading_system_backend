import websocket
import json
import threading
import time
from datetime import datetime
from trading.services.rsi_calculator import update_rsi
from kis.websocket.trading_ws import KISTRADING

## KIS 웹 소켓 API 요청 처리
WS_URL = "wss://openapivts.koreainvestment.com:29443/websocket"

# 구독 메시지 구성
def build_subscribe_message(symbol):
    return {
        "header": {
            "approval_key": "YOUR_APPROVAL_KEY",  # 모의투자용 승인키 (발급받은 값)
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8",
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",  # 국내주식 체결가 실시간
                "tr_key": symbol,  # 예: 005930
            }
        },
    }

def on_message(ws, message):
    try:
        msg = json.loads(message)
        if "body" in msg and "output" in msg["body"]:
            price = float(msg["body"]["output"]["stck_prpr"])
            symbol = msg["body"]["output"]["stck_shrn_iscd"]

            print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol} 체결가={price}")

            # RSI 계산 및 매매 판단
            df = update_rsi(symbol, price)
            rsi = float(df["RSI"].iloc[-1])

            print(f"  RSI={rsi:.2f}")

            if rsi < 5:
                KISTRADING(symbol, action="BUY", price=price)
            elif rsi > 80:
                KISTRADING(symbol, action="SELL", price=price)

    except Exception as e:
        print("[ERROR] on_message:", e)

def on_error(ws, error):
    print("[ERROR]", error)

def on_close(ws, close_status_code, close_msg):
    print("❌ WebSocket 닫힘:", close_msg)

def on_open(ws):
    print("✅ WebSocket 연결됨, 구독 요청 중...")
    time.sleep(1)
    msg = build_subscribe_message("005930")  # 테스트용 삼성전자
    ws.send(json.dumps(msg))

def start_kis_websocket():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()
    print("🚀 실시간 WebSocket 스레드 시작됨")