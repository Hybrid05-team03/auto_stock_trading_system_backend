import requests
import os
from kis.api.auth import _get_headers

BASE_URL = os.getenv("KIS_BASE_URL")
ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")

# KIS 현금 주문 API (시장가 주문)
def place_order(symbol: str, qty: int, side: str):

    # side: BUY / SELL
    tr_id = "TTTC0802U" if side == "BUY" else "TTTC0801U"
    headers = _get_headers(tr_id=tr_id)
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"

    body = {
        "CANO": ACCOUNT_NO[:8],
        "ACNT_PRDT_CD": ACCOUNT_NO[-2:],
        "PDNO": symbol,              # 종목 코드
        "ORD_DVSN": "01",            # 01: 시장가
        "ORD_QTY": str(qty),         # 주문 수량
        "ORD_UNPR": "0",             # 시장가 = 0
    }

    res = requests.post(url, headers=headers, json=body, timeout=10)
    if res.status_code == 200:
        return {"success": True, "data": res.json()}
    else:
        return {"success": False, "error": res.text}