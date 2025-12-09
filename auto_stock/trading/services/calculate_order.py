
def get_tick(price):
    if price < 2000: return 1
    elif price < 5000: return 5
    elif price < 10000: return 10
    elif price < 50000: return 50
    elif price < 100000: return 100
    elif price < 500000: return 500
    elif price < 1000000: return 1000
    else: return 2000


## 매도 목표가 반올림 처리
def normalize_price(price):
    tick = get_tick(price)
    return (price + tick - 1) // tick * tick

## TODO 전일 종가 상하한가 체크
# def clamp_upper_lower(price, symbol):
#     info = kis_get_realtime_price(symbol)  # 전일 종가, 상/하한가 수신
#     upper = info['uplmtprc']
#     lower = info['lwlmtprc']
#
#     return min(max(price, lower), upper)


## 매도 목표가 계산
def calculate_target_price(exec_price: int, target_profit: int) -> int:
    if target_profit == 0:
        print(f"매도가 확인 : {exec_price}")
        return exec_price

    raw_price = exec_price * (1 + target_profit / 100)
    return normalize_price(int(raw_price))