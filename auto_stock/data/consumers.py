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
        logger.debug("[BaseMarketConsumer - __init__] 초기화")
        super().__init__(*args, **kwargs)
        self._task = None

    async def disconnect(self, close_code):
        logger.debug("[BaseMarketConsumer - disconnect] disconnect 진입")
        # 연결 종료 시 백그라운드 태스크를 반드시 취소해야 메모리 누수가 없습니다.
        if self._task and not self._task.done():
            logger.debug("[BaseMarketConsumer - disconnect] 백그라운드 태스크 취소 시도")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.debug("[BaseMarketConsumer - disconnect] 태스크 정상 취소")
                pass
        logger.info(f"WebSocket Disconnected: {self.scope['path']}")

    # JSON Encoding
    @classmethod
    async def encode_json(cls, content):
        logger.debug("[BaseMarketConsumer - encode_json] JSON 인코딩")
        return json.dumps(content, ensure_ascii=False)

# Indices
class IndicesConsumer(BaseMarketConsumer):
    async def connect(self):
        logger.debug("[IndiciesConsumer - connect] 실행")
        await self.accept()
        logger.debug("[IndiciesConsumer - connect] WebSocket accept 완료")

        logger.debug("[IndiciesConsumer - connect] get_realtime_index_payload() 비동기 호출 전")
        payload = await sync_to_async(get_realtime_index_payload)()
        logger.debug("[IndiciesConsumer - connect] get_realtime_index_payload() 비동기 호출 후")

        logger.debug("[IndiciesConsumer - connect] payload 전송 전")
        await self.send_json(payload)
        logger.debug("[IndiciesConsumer - connect] payload 전송 후")

        logger.debug("[IndiciesConsumer - connect] push loop 태스크 생성")
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        logger.debug("[IndiciesConsumer - _push_loop] 시작")
        try:
            while True:
                await asyncio.sleep(5)
                logger.debug("[IndiciesConsumer - _push_loop] get_realtime_index_payload 비동기 호출 전")
                payload = await sync_to_async(get_realtime_index_payload)()
                logger.debug("[IndiciesConsumer - _push_loop] get_realtime_index_payload 비동기 호출 후")

                logger.debug("[IndiciesConsumer - _push_loop] payload 전송 전")
                if payload["indices"]:
                    await self.send_json(payload)
                logger.debug("[IndiciesConsumer - _push_loop] payload 전송 후")
        except asyncio.CancelledError:
            logger.debug("[IndiciesConsumer - _push_loop] 태스크 취소")
            pass # 정상 종료

# Top 10
class RankConsumer(BaseMarketConsumer):
    async def connect(self):
        logger.debug("[RankConsumer - connect] 실행")
        await self.accept()
        logger.debug("[RankConsumer - connect] WebSocket accept 완료")

        logger.debug("[RankConsumer - connect] get_popular_rank_payload 비동기 호출 전")
        payload = await sync_to_async(get_popular_rank_payload)()
        logger.debug("[RankConsumer - connect] get_popular_rank_payload 비동기 호출 후")

        logger.debug("[RankConsumer - connect] payload 전송 전")
        await self.send_json({
            "rank": payload.get("rank", [])
        })
        logger.debug("[RankConsumer - connect] payload 전송 후")

        logger.debug("[RankConsumer - connect] push loop 태스크 생성")
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        logger.debug("[RankConsumer - _push_loop] 시작")
        try:
            while True:
                await asyncio.sleep(30)
                logger.debug("[RankConsumer - _push_loop] get_popular_rank_payload 비동기 호출 전")
                payload = await sync_to_async(get_popular_rank_payload)()
                logger.debug("[RankConsumer - _push_loop] get_popular_rank_payload 비동기 호출 후")

                logger.debug("[RankConsumer - _push_loop] payload 전송 전")
                await self.send_json({
                    "rank": payload.get("rank", [])
                })
                logger.debug("[RankConsumer - _push_loop] payload 전송 후")
        except asyncio.CancelledError:
            logger.debug("[RankConsumer - _push_loop] 태스크 취소")
            pass

# Stock price
class StockPriceConsumer(BaseMarketConsumer):
    async def connect(self):
        logger.debug("[StockPriceConsumer - connect] 실행")

        # Read Parameters
        codes_str = self.scope['url_route']['kwargs'].get('codes', "")
        logger.debug(f"[StockPriceConsumer - connect] codes 파라미터: {codes_str}")
        
        if not codes_str:
            logger.debug("[StockPriceConsumer - connect] codes 없음 → 연결 종료")
            await self.close()
            return

        await self.accept()
        logger.debug("[StockPriceConsumer - connect] WebSocket accept 완료")

        # Parse Parameters
        self.target_codes = [c.strip() for c in codes_str.split(",") if c.strip()]
        logger.debug(f"[StockPriceConsumer - connect] 파싱된 target_codes: {self.target_codes}")

        # Send Data
        logger.debug("[StockPriceConsumer - connect] get_realtime_stock_payload 비동기 호출 전")
        payload = await sync_to_async(get_realtime_stock_payload)(self.target_codes)
        logger.debug("[StockPriceConsumer - connect] get_realtime_stock_payload 비동기 호출 후")

        logger.debug("[StockPriceConsumer - connect] payload 전송 전")
        await self.send_json(payload)
        logger.debug("[StockPriceConsumer - connect] payload 전송 후")

        logger.debug("[StockPriceConsumer - connect] push loop 태스크 생성")
        self._task = asyncio.create_task(self._push_loop())

    async def _push_loop(self):
        logger.debug("[StockPriceConsumer - _push_loop] 시작")
        try:
            while True:
                await asyncio.sleep(5)

                # Update Data
                logger.debug("[StockPriceConsumer - _push_loop] get_realtime_stock_payload 비동기 호출 전")
                payload = await sync_to_async(get_realtime_stock_payload)(self.target_codes)
                logger.debug("[StockPriceConsumer - _push_loop] get_realtime_stock_payload 비동기 호출 후")

                logger.debug("[StockPriceConsumer - _push_loop] payload 전송 전")
                await self.send_json(payload)
                logger.debug("[StockPriceConsumer - _push_loop] payload 전송 후")
        except asyncio.CancelledError:
            logger.debug("[StockPriceConsumer - _push_loop] 태스크 취소")
            pass