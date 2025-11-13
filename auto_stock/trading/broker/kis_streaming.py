import websockets
import json
from trading.services.rsi_decision import handle_realtime_price
from kis.auth.kis_ws_key import get_web_socket_key

async def subscribe(symbol: str):
    url = "wss://openapi.koreainvestment.com:9443/websocket"
    web_socket_key = get_web_socket_key()

    async with websockets.connect(url) as ws:
        # 구독 요청 메시지
        await ws.send(json.dumps({
            "header": {"approval_key": f"{web_socket_key}", "tr_type": "1"},
            "body": {"tr_id": "H0STCNT0", "symbol": symbol}
        }))

        async for message in ws:
            data = json.loads(message)
            await handle_realtime_price(symbol, data)