import requests
import os
import time

from typing import Literal
from kis.api.util.request import _get_headers
from trading.data.trading_result import TradeResult

# --- 환경 변수 ---
BASE_URL = os.getenv("KIS_BASE_URL")
KIS_WS_BASE_URL = os.getenv("KIS_WS_BASE_URL")
ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")

# --- 데이터 모델 ---
Side = Literal["BUY", "SELL"]
OrderType = Literal["limit", "market"] # 지정가, 시장가
RunMode = Literal["real", "mock"] # 실전, 모의

# 한국투자증권 모의 주문 API 호출
class KISTRADING:

    def __init__(self, dry_run: bool = False):
        if not all([BASE_URL, ACCOUNT_NO]):
            raise ValueError("KIS 관련 환경변수가 설정되지 않았습니다. (KIS_BASE_URL, KIS_ACCOUNT_NO)")

        self.dry_run = dry_run
        self.cano, self.acnt_prdt_cd = ACCOUNT_NO.split('-')

    def _get_tr_id(self, side: Side) -> str:
        if side == "BUY":
            return "TTTC0011U" # 매수
        else:
            return "TTTC0012U" # 매도

    def place_order(self, symbol: str, side: Side, qty: int,
        order_type: OrderType = "limit", price: int = 0) -> TradeResult:

        if order_type == "market":
            price = 0 # 시장가 주문 시 가격은 0

        if self.dry_run:
            msg = f"[DryRun] {side} {symbol} x {qty} @{price if price > 0 else 'market'}"
            print(msg)
            return TradeResult(True, side, symbol, qty, price, order_type, "dry-run-order-id", msg)

        ## KIS 주문 API 요청 준비
        tr_id = self._get_tr_id(side)
        headers = _get_headers(tr_id=tr_id)
        endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
        time.sleep(0.05)
        url = f"{KIS_WS_BASE_URL}{endpoint}"

        body = {
            "CANO": self.cano, # 계좌 번호
            "ACNT_PRDT_CD": self.acnt_prdt_cd, # 계좌 상품 코드
            "PDNO": symbol, # 상품 번호
            "ORD_DVSN": "00" if order_type == "limit" else "01",  # 주문 구분: 지정가/시장가
            "ORD_QTY": str(qty), # 주문 수량
            "ORD_UNPR": str(price), # 주문 단가
        }

        try:
            res = requests.post(url, headers=headers, data=body, timeout=10)  # ✅ data=body 로 변경
            res.raise_for_status()

            data = res.json()
            if data["rt_cd"] == "0":
                order_id = data["output"]["ODNO"]
                msg = f"[ SUCCESS ] : 주문 성공 {side} {symbol} x {qty} (주문번호: {order_id})"
                print(msg)
                return TradeResult(True, side, symbol, qty, price, order_type, order_id, msg)
            else:
                msg = f"[FAIL] : 주문 실패 {data['msg1']}"
                print(msg)
                return TradeResult(False, side, symbol, qty, price, order_type, message=data.get("msg1", res.text))

        except requests.exceptions.RequestException as e:
            msg = f"[FAIL] : 주문 실패 {e}"
            print(msg)
            return TradeResult(False, side, symbol, qty, price, order_type, message=str(e))