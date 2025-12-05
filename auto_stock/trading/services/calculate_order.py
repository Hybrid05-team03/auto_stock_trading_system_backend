
def get_tick(price: int) -> int:
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 10000: return 10
    elif price < 50000: return 50
    elif price < 100000: return 100
    elif price < 500000: return 500
    else: return 1000


## 매도 목표가 반올림 처리
def normalize_price(price: int) -> int:
    tick = get_tick(price)
    return (price // tick) * tick


## 매도 목표가 계산
def calculate_target_price(exec_price: int, target_profit: int) -> int:
    if target_profit == 0:
        return exec_price

    raw_price = exec_price * (1 + target_profit / 100)
    return normalize_price(int(raw_price))