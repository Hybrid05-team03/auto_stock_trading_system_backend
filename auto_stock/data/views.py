import os, redis, logging
import time
import pandas as pd

from rest_framework.response import Response
from rest_framework.views import APIView

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series, get_or_set_index_yesterday
from kis.api.index import fetch_overseas_index_snapshot, fetch_domestic_index_snapshot
from kis.api.quote import kis_get_market_cap, kis_get_price_rest
from kis.api.rank import fetch_top10_symbols
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data, get_cached_data
from kis.constants.const_index import INDEX_CODE_NAME_MAP, OVERSEAS_INDEX_CODE_NAME_MAP
from kis.api.util.market_time import is_after_market_close
from data.services.realtime_index import get_realtime_index_payload
from data.services.realtime_rank import get_popular_rank_payload
from data.services.realtime_stock_price import get_realtime_stock_payload
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Token View
class TokenStatusView(APIView):
    def get(self, request):
        return Response(get_token())


# 과거 일봉 조회
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


# 실시간 시세 조회 (WebSocket → Redis)
class RealtimeQuoteView(APIView):
    def get(self, request):
        logger.debug("[RealtimeQuoteView - get]")

        raw_codes = request.query_params.get("codes", "")
        logger.debug(f"[RealtimeQuoteView - get] raw codes 파라미터: {raw_codes}")

        codes = [c.strip() for c in raw_codes.split(",") if c.strip()]
        logger.debug(f"[RealtimeQuoteView - get] 파싱된 codes: {codes}")

        if not codes:
            logger.debug("[RealtimeQuoteView - get] codes 없음 → 400 반환")
            return Response({"detail": "codes is required"}, status=400)

        logger.debug("[RealtimeQuoteView - get] get_realtime_stock_payload 호출 전")
        payload = get_realtime_stock_payload(codes)
        logger.debug("[RealtimeQuoteView - get] get_realtime_stock_payload 호출 후")

        logger.debug("[RealtimeQuoteView - get] payload 생성 완료")
        logger.debug("[RealtimeQuoteView - get] 종료")
        return Response(payload, status=200)


# 실시간 지수 조회 (WebSocket + REST)
class RealtimeIndexView(APIView):
    def get(self, request):
        logger.debug("[RealtimeIndexView - get]")

        logger.debug("[RealtimeIndexView - get] get_realtime_index_payload 호출 전")
        payload = get_realtime_index_payload()
        logger.debug("[RealtimeIndexView - get] get_realtime_index_payload 호출 후")

        logger.debug("[RealtimeIndexView - get] 종료")
        return Response(payload, status=200)



# 인기 종목 조회
class PopularStockRankingView(APIView):
    def get(self, request):
        logger.debug("[PopularStockRankingView - get]")

        logger.debug("[PopularStockRankingView - get] get_popular_rank_payload 호출 전")
        payload = get_popular_rank_payload()
        logger.debug("[PopularStockRankingView - get] get_popular_rank_payload 호출 후")

        logger.debug("[PopularStockRankingView - get] 종료")
        return Response(payload, status=200)