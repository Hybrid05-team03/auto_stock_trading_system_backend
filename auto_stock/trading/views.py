from rest_framework.decorators import api_view
from rest_framework.response import Response
from trading.strategy.rsi_signal import get_trade_signal
from trading.broker.kis_order import place_order

# rsi 지표 분석 후 매수/매도 시그널 (실시간 처리 적용 X 상태)
@api_view(["POST"])
def rsi_trade_view(request, symbol):

    signal = get_trade_signal(symbol)
    action = signal["action"]

    if action == "BUY":
        order = place_order(symbol, qty=1, side="BUY")
        signal["order_result"] = order
    elif action == "SELL":
        order = place_order(symbol, qty=1, side="SELL")
        signal["order_result"] = order
    else:
        signal["order_result"] = {"message": "매매 없음"}

    return Response(signal)

