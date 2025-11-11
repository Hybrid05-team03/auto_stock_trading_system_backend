import websockets
import json
from trading.strategy.rsi_strategy import handle_realtime_price

async def subscribe(symbol: str):
    url = "wss://openapi.koreainvestment.com:9443/websocket"
    async with websockets.connect(url) as ws:
        # 구독 요청 메시지
        await ws.send(json.dumps({
            "header": {"approval_key": "발급받은_웹소켓키", "tr_type": "1"},
            "body": {"tr_id": "H0STCNT0", "symbol": symbol}
        }))

        async for message in ws:
            data = json.loads(message)
            await handle_realtime_price(symbol, data)