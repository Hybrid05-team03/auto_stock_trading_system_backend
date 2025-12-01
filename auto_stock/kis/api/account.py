import os, logging, json, requests
from datetime import datetime
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
    tr_id = "VTTC8434R"

    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "OFL_YN": "N",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    data = request_get(path, tr_id, params)

    print("🔍 RAW OUTPUT1:", data.get("output1"))
    print("FULL RESPONSE:", json.dumps(data, indent=2, ensure_ascii=False))

    # 보유 종목 리스트
    stocks = []
    for s in data.get("output1", []):
        stocks.append({
            "symbol": s["pdno"],
            "name": s["prdt_name"],
            "quantity": int(s["hldg_qty"]),
            "sell_psbl_qty": int(s["ord_psbl_qty"]),
            "current_price": int(s["prpr"]),
            "eval_amt": int(s["evlu_amt"]),
        })

    # 예수금
    output2 = data.get("output2", [{}])
    cash = int(output2[0].get("prvs_rcdl_excc_amt", 0))

    return {
        "cash": cash,
        "stocks": stocks
    }


## 최근 체결가 조회
def fetch_recent_ccld(kis_order_id: str, symbol: str):
    path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    tr_id = "VTTC0081R"

    today = datetime.today().strftime("%Y%m%d")

    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "INQR_STRT_DT": today,
        "INQR_END_DT": today,
        "SLL_BUY_DVSN_CD": "00",
        "PDNO": symbol,  # 상품 번호
        "ORD_GNO_BRNO": "",
        "ODNO": kis_order_id, # 주문 번호
        "CCLD_DVSN": "01",   # 체결된 건만 조회
        "INQR_DVSN": "00",
        "INQR_DVSN_1": "0",
        "INQR_DVSN_3": "00",
        "EXCG_ID_DVSN_CD": "KRX",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    data = request_get(path, tr_id, params)

    if data.get("rt_cd") != "0":
        logger.info(f"[ERROR] 오류 발생: {data.get('msg1')}")
        return None

    output1 = data.get("output1", [])
    if not output1:
        logger.info("체결 내역 없음")
        return None

    # 가장 최신 체결 데이터 (역순 기준)
    latest = output1[0]

    return {
        "date": str(latest.get("ord_dt")),
        "time": str(latest.get("ord_tmd")),
        "price": int(latest.get("avg_prvs", 0)),
        "qty": int(latest.get("tot_ccld_qty", 0))
    }