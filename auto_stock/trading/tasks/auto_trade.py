from auto_stock.celery import app
from trading.models import OrderRequest
from kis.websocket.trading_ws import order_buy, order_sell
from trading.services.rsi_process import get_rsi_signal

@app.task
def auto_trade(order_id):
    order = OrderRequest.objects.get(id=order_id)

    # 상태 변경
    order.status = "PROCESSING"
    order.save()

    signal, rsi = get_rsi_signal(order.symbol, period=14)
    # RSI 기반 매매 신호 계산

    if not signal:
        order.status = "FAIL"
        order.message = f"RSI 기준 매매 신호 없음 (RSI={rsi})"
        order.save()
        return

    # 신호에 따른 주문 실행
    if signal == "BUY":
        result = order_buy(order.symbol, qty=order.quantity, order_type="market")
    else:
        result = order_sell(order.symbol, qty=order.quantity, order_type="market")

    # DB 저장
    order.status = "SUCCESS" if result.ok else "FAIL"
    order.message = result.message
    order.save()