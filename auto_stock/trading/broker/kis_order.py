import requests
import os
from datetime import datetime
from kis.api.auth import _get_headers, _get_token

BASE_URL = os.getenv("KIS_BASE_URL")
ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
CANO = os.getenv("KIS_CANO")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD")

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

def _auth_headers(tr_id: str):
    """KIS 요청에 필요한 공통 헤더 생성"""
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {_get_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,  # 모의투자: VTTC0802U / 실전: TTTC0802U
    }

def place_order(symbol: str, action: str, price: float, qty: int = 1):
    """
    KIS OpenAPI 매수/매도 주문
    """
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order"

    if action.upper() == "BUY":
        tr_id = "VTTC0802U"  # 모의투자 매수
        order_type = "2"     # 매수
    elif action.upper() == "SELL":
        tr_id = "VTTC0801U"  # 모의투자 매도
        order_type = "1"     # 매도
    else:
        raise ValueError("Invalid action. Must be BUY or SELL")

    payload = {
        "CANO": ACCOUNT_NO.split('-')[0],         # 계좌번호 앞 8자리
        "ACNT_PRDT_CD": ACCOUNT_NO.split('-')[1], # 계좌번호 뒤 2자리
        "PDNO": symbol,                           # 종목코드
        "ORD_DVSN": "00",                         # 지정가 주문
        "ORD_QTY": str(qty),                      # 주문수량
        "ORD_UNPR": str(price),                   # 주문단가
    }

    headers = _auth_headers(tr_id)
    res = requests.post(url, headers=headers, json=payload)

    # 응답 결과 처리
    if res.status_code != 200:
        return {"status": "error", "message": res.text}

    data = res.json()
    output = data.get("output", {})

    return {
        "status": "success",
        "symbol": symbol,
        "action": action,
        "price": price,
        "qty": qty,
        "order_no": output.get("ODNO", "N/A"),
        "order_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }