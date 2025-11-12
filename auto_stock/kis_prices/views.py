from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import fetch_price_series


class DailyPriceView(APIView):
    """
    REST endpoint that proxies normalized daily closing prices.
    """

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
