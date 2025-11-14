# trading/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response

from trading.tasks import run_auto_trading


# -------------------------------------------------------
# 실시간 자동매매 시작 (Celery 트리거)
# -------------------------------------------------------
@api_view(["POST"])
def start_auto_trading(request):
    symbol = request.query_params.get("code")

    if not symbol:
        return Response({"error": "code 쿼리 파라미터가 필요합니다."}, status=400)

    run_auto_trading.delay(symbol)

    return Response({
        "message": f"{symbol} 자동매매 작업이 Celery 워커에서 실행됩니다.",
        "symbol": symbol
    })