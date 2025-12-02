import os, redis, logging
import time

from rest_framework.response import Response
from rest_framework.views import APIView

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series, get_or_set_index_yesterday
from kis.api.index import fetch_overseas_index_snapshot
from kis.api.quote import kis_get_market_cap
from kis.api.rank import fetch_top10_symbols
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data, get_cached_data
from kis.constants.const_index import INDEX_CODE_NAME_MAP, OVERSEAS_INDEX_CODE_NAME_MAP
from kis.api.util.market_time import is_after_market_close


logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

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
        tr_id = os.getenv("PRICE_REALTIME_TR_ID")
        if not codes:
            return Response({"detail": "codes is required"}, status=400)

        results = []
        # 장 운영 시간인지 확인 (True=장중, False=장마감)
        # is_after_market_close() returns True if market is OPEN, False if CLOSED (based on user info)
        is_market_open = is_after_market_close()

        for code in codes:
            if is_market_open:
                data = subscribe_and_get_data(tr_id, code, "price", timeout=10)
            else:
                data = get_cached_data(code, "price")

            stock_name = mapping_code_to_name(code)
            if data:
                result_item = {
                    "name": stock_name,
                    "code": code,
                    "price": kis_get_market_cap(code),
                    "currentPrice": data.get("current_price"),
                    "changePercent": data.get("change_rate"),
                    "volume": data.get("trade_value"),
                }
                results.append(result_item)
            else:
                results.append({
                    "name": stock_name,
                    "code": code,
                    "status": "timeout and no cached data"
                })

        return Response({"stock": results}, status=200)


# ------------------------------------------------------------
# 실시간 지수 조회 (WebSocket + REST)
# ------------------------------------------------------------
class RealtimeIndexView(APIView):
    def get(self, request):
        tr_id = os.getenv("INDEX_REALTIME_TR_ID")
        results = []

        # 1) 국내 지수 2종 (코스피/코스닥) - WebSocket
        # 장 운영 시간인지 확인 (True=장중, False=장마감)
        # is_after_market_close() returns True if market is OPEN, False if CLOSED (based on user info)

        is_market_open = is_after_market_close()

        for code, name in INDEX_CODE_NAME_MAP.items():
            yesterday = get_or_set_index_yesterday(code)
            
            if is_market_open:
                ws_data = subscribe_and_get_data(tr_id, code, "index", timeout=3)
            else:
                ws_data = get_cached_data(code, "index")

            if ws_data and ws_data.get("price"):
                results.append({
                    "name": name,
                    "yesterday": yesterday,
                    "today": ws_data["price"],
                })

        # 2) 해외 지수 2종 (달러환율 / 나스닥100) - REST
        for index_key in OVERSEAS_INDEX_CODE_NAME_MAP.keys():
            snap = fetch_overseas_index_snapshot(index_key)
            if not snap:
                continue

            results.append({
                "name": snap["name"],
                "yesterday": snap.get("yesterday"),
                "today": snap["today"],
            })

        if results:
            return Response({"indices": results})
        return Response({"message": "incomplete index data"}, status=204)


## 인기 종목 조회
class PopularStockRankingView(APIView):
    def get(self, request):
        return Response({"rank": fetch_top10_symbols(10)})