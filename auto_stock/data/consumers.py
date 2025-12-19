import asyncio
import os
import logging
import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async

from data.services.realtime_index import get_realtime_index_payload

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL = int(os.getenv("WS_INDICES_INTERVAL", "5"))  # 5 sec


class IndicesConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task = None
        self._interval = DEFAULT_INTERVAL

    async def connect(self):
        await self.accept()

        # 1) 접속 즉시 snapshot 1회
        payload = await sync_to_async(get_realtime_index_payload)()
        await self.send_json({"type": "snapshot", "data": payload})

        # 2) 주기 갱신 시작
        self._task = asyncio.create_task(self._push_loop())

    async def disconnect(self, close_code):
        # 주기 태스크 종료
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _push_loop(self):
        last = None
        while True:
            try:
                await asyncio.sleep(self._interval)
                payload = await sync_to_async(get_realtime_index_payload)()

                cur = json.dumps(payload, sort_keys=True)
                if cur != last:
                    last = cur
                    await self.send_json({"type": "update", "data": payload})            
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("WS indices push loop error")
                await asyncio.sleep(self._interval)

    # 프론트에서 갱신 주기 변경 가능
    # async def receive_json(self, content, **kwargs):
    #     action = content.get("action")
    #     if action == "refresh":
    #         payload = await sync_to_async(get_realtime_index_payload)()
    #         await self.send_json({"type": "update", "data": payload})
    #     elif action == "set_interval":
    #         sec = int(content.get("seconds", DEFAULT_INTERVAL))
    #         self._interval = max(1, min(sec, 60))  # 1~60초 제한
    #         await self.send_json({"type": "ack", "interval": self._interval})
