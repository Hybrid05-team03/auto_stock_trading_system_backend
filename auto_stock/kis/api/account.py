import os, logging

from kis.api.util.request import request_get

BASE_URL = os.getenv("KIS_BASE_URL")
ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")
CANO, ACNT_PRDT_CD = ACCOUNT_NO.split("-")
TR_ID = "VTTC8908R"

logger = logging.getLogger(__name__)

## 특정 종목 매수 가능 조회 (모의)
def fetch_psbl_order(symbol: str):
    path = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
    tr_id = "VTTC8908R"

    params = {
        "CANO": "50156403",
        "ACNT_PRDT_CD": "01",
        "PDNO": symbol,
        "ORD_DVSN": "01",     # 시장가
        "ORD_UNPR": "",       # 시장가이므로 공란
        "CMA_EVLU_AMT_ICLD_YN": "N",
        "OVRS_ICLD_YN": "N"
    }

    try:
        data = request_get(path, tr_id, params)

        output = data.get("output", {})

        clean = {
            "symbol": symbol,
            "buyableQty": int(output.get("max_buy_qty", 0)),
            "buyableAmount": int(output.get("max_buy_amt", 0)),
            "availableCash": int(output.get("ord_psbl_cash", 0)),
            "message": data.get("msg1", "").strip(),
        }

        return clean

    except Exception as e:
        return {"error": str(e)}


## 계좌 보유 잔고 조회 (모의)
def fetch_balance():
    path = "/uapi/domestic-stock/v1/trading/inquire-balance"
    tr_id = "VTTC8434R"   # 모의 계좌 잔고조회 TR-ID

    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "INQR_DVSN": "01",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        data = request_get(path, tr_id, params)

        balance_info = {
            "cash": data.get("output2", [{}])[0].get("prvs_rcdl_excc_amt", 0),
            "stocks": []
        }

        stock_list = data.get("output1", [])

        for s in stock_list:
            balance_info["stocks"].append({
                "symbol": s.get("pdno"),                          # 종목코드
                "name": s.get("prdt_name"),                       # 종목명
                "quantity": int(s.get("hldg_qty", 0)),            # 보유수량
                "sell_psbl_qty": int(s.get("sell_psbl_qty", 0)),  # 매도가능수량
                "current_price": int(s.get("prpr", 0)),           # 현재가
                "eval_amt": int(s.get("evlu_amt", 0)),            # 평가금액
            })

        return balance_info

    except Exception as e:
        logger.error(f"[KIS ERROR] ERROR : {e}")
        return None