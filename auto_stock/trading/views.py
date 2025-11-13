from trading.services.rsi_decision import get_static_signal
from kis.websocket.trading_ws import KISTRADING
from rest_framework.decorators import api_view
from rest_framework.response import Response
from trading.tasks import run_auto_trading

## rsi 지표 분석 후 매수/매도 시그널 (실시간 처리 적용 X 상태)
@api_view(["POST"])
def rsi_trade_view(request, symbol):

    signal = get_static_signal(symbol)
    action = signal["action"]

    if action == "BUY":
        order = KISTRADING(symbol, qty=1, side="BUY")
        signal["order_result"] = order
    elif action == "SELL":
        order = KISTRADING(symbol, qty=1, side="SELL")
        signal["order_result"] = order
    else:
        signal["order_result"] = {"message": "매매 없음"}

    return Response(signal)

## 실시간 주문 요청
@api_view(["POST"])
def start_auto_trading(request, symbol):
    run_auto_trading.delay(symbol)
    return Response({"message": f"{symbol} 자동매매 작업이 Celery로 실행됨"})