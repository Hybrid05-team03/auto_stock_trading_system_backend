import os
import json
import redis
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RealtimeSymbol
from .serializers import RealtimeSymbolSerializer

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series

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


## kis/websocket 실시간 종목 조회 (WebSocket)
class RealtimeSymbolView(APIView):
    def get(self, request):
        serializer = RealtimeSymbolSerializer(RealtimeSymbol.objects.all(), many=True)
        return Response({"symbols": serializer.data})

    def post(self, request):
        serializer = RealtimeSymbolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        obj, created = RealtimeSymbol.objects.update_or_create(
            identifier=payload["identifier"],
            defaults={"code": payload["code"], "name": payload.get("name", "")},
        )

        # Redis 구독 요청 (quote 타입으로 고정)
        publish_subscription_request(
            tr_id="H0STASP0",
            tr_key=payload["code"],
            sub_type="quote"
        )

        response_serializer = RealtimeSymbolSerializer(obj)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=status_code)


### tmp/websocket 실시간 시세 조회 (WebSocket)
class RealtimeQuoteView(APIView):
    def get(self, request):
        raw_codes = request.query_params.get("codes", "")
        codes = [c.strip() for c in raw_codes.split(",") if c.strip()]

        if not codes: # 종목 코드 없는 경우
            return Response(
                {"detail": "Query parameter 'codes' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        for code in codes: # 종목 코드 별 웹소켓 구독 요청
            redis_key = f"quote:{code}"
            cached = r.get(redis_key)

            if not cached:
                publish_subscription_request(
                    tr_id="H0STCNT0",
                    tr_key=code,
                    sub_type="quote"
                )
                results.append({"code": code, "status": "subscribe add requested"})
                continue

            try:
                data = json.loads(cached)
                results.append({
                    "code": data.get("symbol", code),
                    "quote": data.get("quote"),
                    "time": data.get("time"),
                })
            except Exception:
                results.append({"code": code, "error": "parse error"})

        return Response({"quotes": results})