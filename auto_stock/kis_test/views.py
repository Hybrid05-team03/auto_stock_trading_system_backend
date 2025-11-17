from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RealtimeSymbol
from .serializers import RealtimeSymbolSerializer

from kis.auth.kis_token import get_token
from kis.api.price import fetch_price_series
from kis.websocket.quote_ws import fetch_realtime_quote


## kis/auth 토큰 발급
class TokenStatusView(APIView):
    def get(self, request):
        return Response(get_token())


## kis/websocket 실시간 종목 조회
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
        response_serializer = RealtimeSymbolSerializer(obj)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=status_code)


### kis/websocket 실시간 시세 조회
class RealtimeQuoteView(APIView):
    def get(self, request):
        raw_codes = request.query_params.get("codes", "")
        codes = [c.strip() for c in raw_codes.split(",") if c.strip()]


        if not codes:
            return Response(
                {"detail": "Query parameter 'codes' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # 종목 코드 ","로 구분하여 요청 (ex: 005930,000660)
        results = []

        for code in codes:
            data = fetch_realtime_quote(
                endpoint="/tryitout/",
                symbol=code,
                tr_id="H0STCNT0"
            )

            if not data:
                results.append({"code": code, "error": "no data"})
                continue

            results.append({
                "code": data["symbol"],
                "price": data["price"],
                "change": data["change"],
                "change_sign": data["change_sign"],
                "change_rate": data["change_rate"],
                "trade_value": data["trade_value"],
                "timestamp": data["timestamp"],
            })
        return Response({"quotes": results})


## kis/api 가격 조회
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