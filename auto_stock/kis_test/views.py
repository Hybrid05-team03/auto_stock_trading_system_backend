import os, json
import redis
import logging
import time
from datetime import datetime

from redis import Redis

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series, get_or_set_index_yesterday
from kis.constants.const_index import INDEX_CODE_NAME_MAP
from kis.api.rank import load_top10_symbols

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


## tmp/auth_temp 토큰 발급 (REST)
class TokenStatusView(APIView):
    def get(self, request):
        return Response(get_token())


## kis/api 가격 조회 (REST)
class DailyPriceView(APIView):
    def get(self, request):
        symbol = request.query_params.get("symbol")
        period = request.query_params.get("period", "D")
        if not symbol:
            return Response(
                {"detail": "Query parameter 'symbol' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            series = fetch_price_series(symbol, period=period)
        except Exception as exc:
            return Response(
                {"detail": f"Failed to fetch data: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"symbol": symbol, "period": period, "series": series})


## 소켓 구독 요청을 위한 공통 함수
def publish_subscription_request(tr_id: str, tr_key: str, sub_type: str):
    """Redis pub/sub 구독 요청 메시지 전송"""
    r.publish("subscribe.add", json.dumps({
        "action": "subscribe",
        "tr_id": tr_id,
        "tr_key": tr_key,
        "type": sub_type
    }))


### tmp/websocket 실시간 시세 조회 (WebSocket- price)
class RealtimeQuoteView(APIView):
    def get(self, request):
        raw_codes = request.query_params.get("codes", "")
        codes = [c.strip() for c in raw_codes.split(",") if c.strip()]

        if not codes:
            return Response(
                {"detail": "Query parameter 'codes' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 종목코드 → 종목명 매핑 로드
        symbols = load_top10_symbols()
        symbol_map = {item["code"]: item["name"] for item in symbols}

        results = []

        for code in codes:
            redis_key = f"price:{code}"
            cached = r.get(redis_key)

            # 캐시가 있으면 즉시 반환
            if cached:
                results.append(self._format_result(cached, code, symbol_map))
                continue

            # 1) 구독 요청 전송
            publish_subscription_request(
                tr_id="H0STCNT0",
                tr_key=code,
                sub_type="price"
            )

            # 2) Redis에 데이터가 들어올 때까지 대기
            data = self._wait_for_redis(redis_key, timeout=2.0)

            if data:
                results.append(self._format_result(data, code, symbol_map))
            else:
                results.append({
                    "name": symbol_map.get(code, code),
                    "code": code,
                    "status": "timeout waiting for realtime price"
                })

        return Response({"stock": results}, status=status.HTTP_200_OK)

    # Redis 대기 함수
    def _wait_for_redis(self, key, timeout=2.0):
        start = time.time()
        while time.time() - start < timeout:
            cached = r.get(key)
            if cached:
                return cached
            time.sleep(0.05)
        return None

    # 응답 포맷
    def _format_result(self, cached, code, symbol_map):
        try:
            data = json.loads(cached)

            return {
                "name": symbol_map.get(code, code),
                "code": code,
                "price": data.get("current_price"),
                "currentPrice": data.get("current_price"),
                "changePercent": data.get("change_rate"),
                "volume": data.get("trade_value")
            }
        except Exception:
            return {"code": code, "error": "parse error"}


## 지수 조회
class RealtimeIndexView(APIView):
    def get(self, request):
        timeout = 2
        start = time.time()
        today_str = datetime.now().strftime("%Y-%m-%d")

        results, timestamps = [], []

        for code, name in INDEX_CODE_NAME_MAP.items():
            # 1️⃣ 전일 종가 가져오기 (지수 코드 전용)
            yesterday_price = get_or_set_index_yesterday(code)

            # 2️⃣ 실시간 Redis 값 수신 대기
            while time.time() - start < timeout:
                redis_key = f"index:{code}"
                cached = r.get(redis_key)

                if not cached:
                    time.sleep(0.2)
                    continue

                try:
                    data = json.loads(cached)
                    results.append({
                        "name": name,
                        "yesterday": yesterday_price,
                        "today": data.get("price")
                    })
                    timestamps.append(data.get("timestamp"))
                    break
                except:
                    time.sleep(0.2)

        if len(results) == len(INDEX_CODE_NAME_MAP):
            ts_min = min(timestamps)[:5]
            ts_max = max(timestamps)[:5]
            if ts_min == ts_max:
                return Response({"indices": results}, status=200)

        return Response(
            {"message": "데이터 동기화 실패 또는 일부 누락"},
            status=204
        )


## 상위 10개 종목 조회
class PopularStockRankingView(APIView):
    def get(self, request):
        data = load_top10_symbols()
        return Response({"rank": data})