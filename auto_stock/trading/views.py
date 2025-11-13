# trading/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response

from trading.services.trading_strategy import determine_signal
from trading.services.trading_rsi_calculate import calculate_rsi
from kis.api.quote import kis_get_last_quote

from trading.tasks import run_auto_trading
from kis.websocket.trading_ws import KISTRADING


# -------------------------------------------------------
# 단발성 RSI 기반 매수/매도 신호 (테스트용)
# -------------------------------------------------------
@api_view(["POST"])
def rsi_trade_view(request, symbol: str):

    df = kis_get_last_quote(symbol, count=100)
    if df.empty:
        return Response({"symbol": symbol, "error": "시세 데이터 없음"}, status=400)

    rsi = float(calculate_rsi(df, period=2).dropna().iloc[-1])
    price = float(df["close"].iloc[-1])

    decision = determine_signal(symbol, rsi, price)

    # 매매 실행 (테스트용)
    if decision.side in ["BUY", "SELL"]:
        result = KISTRADING(
            symbol=symbol,
            qty=1,
            side=decision.side
        )
        decision.order_result = result

    return Response({
        "symbol": symbol,
        "side": decision.side,
        "reason": decision.reason,
        "price": price,
        "rsi": rsi
    })


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