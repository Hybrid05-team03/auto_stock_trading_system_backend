import os
import requests
from typing import Literal
from kis.api.util.request import _get_headers
from trading.data.trading_result import TradeResult

Type = Literal["BUY", "SELL"]
OrderType = Literal["limit", "market"]

BASE_URL = os.getenv("BASE_URL")
ACCOUNT_NO = os.getenv("ACCOUNT_NO")


BUY_TR_ID = os.getenv("BUY_TR_ID")
SELL_TR_ID = os.getenv("SELL_TR_ID")
CANCEL_TR_ID = os.getenv("CANCEL_TR_ID")


CANO, ACNT_PRDT_CD = ACCOUNT_NO.split("-")


if not all([BASE_URL, ACCOUNT_NO, BUY_TR_ID, SELL_TR_ID, CANCEL_TR_ID]):
    raise RuntimeError("KIS 환경변수(BASE_URL, ACCOUNT_NO, BUY_TR_ID, SELL_TR_ID, CANCEL_TR_ID)가 필요합니다.")

## KIS 주문 요청 로직
def _send_order(symbol: str, type: Type, qty: int, price: int,
                order_type: OrderType, dry_run: bool = False) -> TradeResult:

    if order_type == "market":
        price = 0

    if dry_run:
        msg = f"[DryRun] {type} {symbol} x {qty} @{price or 'market'}"
        print(msg)
        return TradeResult(True, type, symbol, qty, price, order_type, "dry-run", msg)

    # TR-ID 선택
    tr_id = BUY_TR_ID if type == "BUY" else SELL_TR_ID
    headers = _get_headers(tr_id=tr_id)

    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"

    body = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": symbol,
        "ORD_DVSN": "00" if order_type == "limit" else "01",
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
    }

    print("[DEBUG] URL:", url)
    print("[DEBUG] BODY:", body)
    print("[DEBUG] HEADERS:", headers)

    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        res.raise_for_status()

        data = res.json()
        if data.get("rt_cd") == "0":
            order_id = data["output"]["ODNO"]
            msg = f"[SUCCESS] {type} {symbol} x {qty} (주문번호 {order_id})"
            print(msg)
            return TradeResult(True, type, symbol, qty, price, order_type, order_id, msg)

        # 실패 메시지
        msg = f"[FAIL] {data.get('msg1', 'Unknown error')}"
        print(msg)
        return TradeResult(False, type, symbol, qty, price, order_type, message=msg)


    except requests.RequestException as e:

        print("[DEBUG] REQUEST EXCEPTION:", e)

        if hasattr(e, "response") and e.response is not None:
            print("[DEBUG] RAW RESPONSE:", e.response.text)

        msg = f"[FAIL] 요청 실패: {e}"

        print(msg)

        return TradeResult(False, type, symbol, qty, price, order_type, message=str(e))


## 매도
def order_sell(symbol: str, qty: int, price: int = 0,
               order_type: OrderType = "limit",
               dry_run: bool = False) -> TradeResult:
    return _send_order(symbol, "SELL", qty, price, order_type, dry_run)


## 매수
def order_buy(symbol: str, qty: int, price: int=0,
              order_type: OrderType = "limit",
              dry_run: bool = False) -> TradeResult:

    return _send_order(symbol, "BUY", qty, price, order_type, dry_run)


## 주문 취소
def order_cancel(symbol: str, order_id: str, qty: int, total: bool = False, dry_run: bool = False) -> TradeResult:
    if dry_run:
        msg = f"[DryRun] CANCEL {symbol} order_id={order_id} qty={'ALL' if total else qty}"
        print(msg)
        return TradeResult(True, "CANCEL", symbol, qty, 0, "market", "dry-run", msg)

    headers = _get_headers(tr_id=CANCEL_TR_ID)
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-rvsecncl"

    body = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "KRX_FWDG_ORD_ORGNO": "00950",  # 한국투자증권 영업점 코드 (가상계좌인 경우 다를 수 있음, 보통 00950/06010 등)
        "ORGN_ODNO": order_id,
        "ORD_DVSN": "00",               # 00: 지정가 (취소는 보통 00)
        "RVSE_CNCL_DVSN_CD": "02",      # 01: 정정, 02: 취소
        "ORD_QTY": "0" if total else str(qty), # 0이면 전량 취소
        "ORD_UNPR": "0",                # 취소는 단가 0
        "QTY_ALL_ORD_YN": "Y" if total else "N",
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        res.raise_for_status()

        data = res.json()
        if data.get("rt_cd") == "0":
            msg = f"[SUCCESS] CANCEL {symbol} order_id={order_id}"
            return TradeResult(True, "CANCEL", symbol, qty, 0, "market", order_id, msg)

        msg = f"[FAIL] {data.get('msg1', 'Unknown error')}"
        return TradeResult(False, "CANCEL", symbol, qty, 0, "market", message=msg)

    except requests.RequestException as e:
        return TradeResult(False, "CANCEL", symbol, qty, 0, "market", message=str(e))

