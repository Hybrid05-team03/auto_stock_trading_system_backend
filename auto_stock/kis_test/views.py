import os, json, redis, logging, time
from datetime import datetime

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series, get_or_set_index_yesterday
from kis.constants.const_index import INDEX_CODE_NAME_MAP
from kis.api.rank import fetch_top10_symbols


logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# ------------------------------------------------------------
# Redis Pub/Sub → WebSocket 구독 요청 발행
# ------------------------------------------------------------
def publish_subscription_request(tr_id: str, tr_key: str, sub_type: str):
    r.publish("subscribe.add", json.dumps({
        "action": "subscribe",
        "tr_id": tr_id,
        "tr_key": tr_key,
        "type": sub_type
    }))


# ------------------------------------------------------------
# Token View
# ------------------------------------------------------------
class TokenStatusView(APIView):
    def get(self, request):
        return Response(get_token())


# ------------------------------------------------------------
# 과거 일봉 조회
# ------------------------------------------------------------
class DailyPriceView(APIView):
    def get(self, request):
        symbol = request.query_params.get("symbol")
        period = request.query_params.get("period", "D")

        if not symbol:
            return Response({"detail": "symbol is required"}, status=400)

        try:
            series = fetch_price_series(symbol, period=period)
            return Response({"symbol": symbol, "period": period, "series": series})
        except Exception as exc:
            return Response({"detail": str(exc)}, status=502)


# ------------------------------------------------------------
# 실시간 시세 조회 (WebSocket → Redis)
# ------------------------------------------------------------
class RealtimeQuoteView(APIView):

    def get(self, request):
        raw_codes = request.query_params.get("codes", "")
        codes = [c.strip() for c in raw_codes.split(",") if c.strip()]

        if not codes:
            return Response({"detail": "codes is required"}, status=400)

        # 종목명 매핑
        symbols = fetch_top10_symbols(10)
        symbol_map = {item["code"]: item["name"] for item in symbols}

        results = []

        for code in codes:
            redis_key = f"price:{code}"

            ## 캐싱 데이터 확인
            cached = r.get(redis_key)
            if cached:
                cached_dict = json.loads(cached)
                results.append(self._format_result(cached_dict, code, symbol_map, cached=True))
                continue


            ## Cache Miss : KIS Websocket 요청
            publish_subscription_request("H0STCNT0", code, "price")

            ## 새 데이터 대기 + fallback
            data = self._wait_for_redis(redis_key, timeout=10.0)

            if data:
                results.append(self._format_result(data, code, symbol_map, cached=False))
            else:
                results.append({
                    "name": symbol_map.get(code, code),
                    "code": code,
                    "status": "timeout and no cached data"
                })

        return Response({"stock": results}, status=200)

    ## Redis 대기 with fallback
    def _wait_for_redis(self, redis_key, timeout=10):
        start = time.time()

        # 1) 새로운 데이터 대기
        while time.time() - start < timeout:
            val = r.get(redis_key)
            if val:
                return json.loads(val)
            time.sleep(0.2)

        # 2) timeout 발생했어도 기존 데이터 있으면 fallback
        val = r.get(redis_key)
        if val:
            return json.loads(val)

        # 3) 진짜 없으면 None
        return None

    ## 응답 변환
    def _format_result(self, data: dict, code, symbol_map, cached=False):
        return {
            "name": symbol_map.get(code, code),
            "code": code,
            "price": data.get("current_price"),
            "currentPrice": data.get("current_price"),
            "changePercent": data.get("change_rate"),
            "volume": data.get("trade_value"),
            "marketCap": data.get("market_cap"),  # 시가 총액
            "source": "cache" if cached else "realtime"
        }


## 지수 조회
class RealtimeIndexView(APIView):
    def get(self, request):
        timeout = 2
        start = time.time()

        results = []
        timestamps = []

        for code, name in INDEX_CODE_NAME_MAP.items():
            yesterday_price = get_or_set_index_yesterday(code)

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
            return Response({"indices": results}, status=200)

        return Response({"message": "incomplete index data"}, status=204)


## 인기 종목 조회
class PopularStockRankingView(APIView):
    def get(self, request):
        return Response({"rank": fetch_top10_symbols(10)})