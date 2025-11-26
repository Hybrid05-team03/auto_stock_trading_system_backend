from auto_stock.celery import app

from kis.websocket.trading_ws import order_sell, order_buy
from trading.models import OrderRequest

@app.task
def process_order(order_id):
    order = OrderRequest.objects.get(id=order_id)
    order.status = "PROCESSING"
    order.save()

    # 실제 KIS 주문 실행
    if order.strategy == "BUY":
        result = order_sell(order.symbol, order.quantity)
    else:
        result = order_buy(order.symbol, order.quantity)

    # 성공/실패 저장
    order.status = "SUCCESS" if result.ok else "FAIL"
    order.save()