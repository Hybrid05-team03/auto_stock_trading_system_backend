import os, redis, logging

from rest_framework.response import Response
from rest_framework.views import APIView

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series, get_or_set_index_yesterday
from kis.api.quote import kis_get_market_cap
from kis.api.rank import fetch_top10_symbols
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data
from kis.constants.const_index import INDEX_CODE_NAME_MAP, ETF_INDEX_MAP


logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
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
        if not codes:
            return Response({"detail": "codes is required"}, status=400)

        results = []
        for code in codes:
            data = subscribe_and_get_data("H0STCNT0", code, "price", timeout=10)
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


## 지수 조회
class RealtimeIndexView(APIView):
    def get(self, request):
        results = []

        # 국내 지수(코스피,코스닥,환율)
        for code, name in INDEX_CODE_NAME_MAP.items():
            yesterday = get_or_set_index_yesterday(code)
            ws_data = subscribe_and_get_data("H0UPCNT0", code, "index", timeout=3)

            if ws_data and ws_data.get("price"):
                results.append({
                    "name": name,
                    "yesterday": yesterday,
                    "today": ws_data["price"],
                })

        # 나스닥(임시 ETF 기반) REST 요청
        nasdaq_info = ETF_INDEX_MAP["nasdaq"]
        code = nasdaq_info["code"]
        name = nasdaq_info["name"]

        series = fetch_price_series(code)
        yesterday = series[1]["close"] if len(series) > 1 else None
        today = series[0]["close"] if series else None

        if today is not None:
            results.append({
                "name": name,
                "yesterday": yesterday,
                "today": today,
            })

        if len(results) >= 3:
            return Response({"indices": results})
        return Response({"message": "incomplete index data"}, status=204)


## 인기 종목 조회
class PopularStockRankingView(APIView):
    def get(self, request):
        return Response({"rank": fetch_top10_symbols(10)})