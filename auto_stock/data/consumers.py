import asyncio, os, logging, json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async

from data.services.realtime_index import get_realtime_index_payload
from data.services.realtime_rank import get_popular_rank_payload
from data.services.realtime_stock_price import get_realtime_stock_payload

logger = logging.getLogger(__name__)

# 중복 코드를 줄이기 위한 기본 클래스
class BaseMarketConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task = None

    async def disconnect(self, close_code):
        # 연결 종료 시 백그라운드 태스크를 반드시 취소해야 메모리 누수가 없습니다.
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"WebSocket Disconnected: {self.scope['path']}")
    # JSON Encoding
    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, ensure_ascii=False)

# Indices
class IndicesConsumer(BaseMarketConsumer):
    async def connect(self):
        await self.accept()
        payload = await sync_to_async(get_realtime_index_payload)()
        await self.send_json(payload)
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        try:
            while True:
                await asyncio.sleep(5)
                payload = await sync_to_async(get_realtime_index_payload)()
                if payload["indices"]:
                    await self.send_json(payload)
        except asyncio.CancelledError:
            pass # 정상 종료

# Top 10
class RankConsumer(BaseMarketConsumer):
    async def connect(self):
        await self.accept()
        payload = await sync_to_async(get_popular_rank_payload)()
        await self.send_json({
            "rank": payload.get("rank", [])
        })
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        try:
            while True:
                await asyncio.sleep(30)
                payload = await sync_to_async(get_popular_rank_payload)()
                await self.send_json({
                    "rank": payload.get("rank", [])
                })
        except asyncio.CancelledError:
            pass

# Stock price
class StockPriceConsumer(BaseMarketConsumer):
    async def connect(self):
        # Read Parameters
        codes_str = self.scope['url_route']['kwargs'].get('codes', "")
        
        if not codes_str:
            await self.close()
            return

        await self.accept()

        # Parse Parameters
        self.target_codes = [c.strip() for c in codes_str.split(",") if c.strip()]
        
        # Send Data
        payload = await sync_to_async(get_realtime_stock_payload)(self.target_codes)
        await self.send_json(payload)        
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        try:
            while True:
                await asyncio.sleep(5)

                # Update Data
                payload = await sync_to_async(get_realtime_stock_payload)(self.target_codes)
                await self.send_json(payload)
        except asyncio.CancelledError:
            pass