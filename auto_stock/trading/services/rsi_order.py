# trading/services/order_service.py
from kis.api.price import kis_get_realtime_price
from kis.websocket.trading_ws import order_sell, order_buy

def execute_order_by_signal(symbol: str, signal: str, qty: int = 1):
    """
    RSI 신호 기반 주문 실행
    BUY → 현재가 지정가
    SELL → 현재가 지정가
    """
    current = kis_get_realtime_price(symbol)

    if current <= 0:
        print(f"[ERROR] 현재가 불러오기 실패: {symbol}")
        return None

    price = current  # RSI 전략 기본 지정가

    if signal == "BUY":
        return order_sell(symbol, qty, price, order_type="limit")

    elif signal == "SELL":
        return order_buy(symbol, qty, price, order_type="limit")

    return None