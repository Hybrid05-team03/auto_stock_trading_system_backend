import os
import time
from .symbols import INDICES

from kis.api.util.request import request_get
from kis.websocket.quote_ws import fetch_realtime_quote, REALTIME_TR_ID

# 간단 캐시/스로틀: 잦은 새로고침 시 KIS 호출 제한
_CACHE_TTL = int(os.getenv("INDICES_CACHE_TTL_SECONDS", "5"))
_STATE = {"last_payload": None, "last_at": 0.0}

# ETF 대체 코드 (KRX)
SYMBOLS = {
    "exchangeRate": "261240",  # KODEX 미국달러선물
    "kospi": "069500",         # KODEX 200
    "kosdaq": "229200",        # KODEX 코스닥150
    "nasdaq": "133690",        # TIGER 미국나스닥100
}

# 국내 일자별 시세
TR_ID_DAILY = "FHKST01010400"
PATH_DAILY  = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"

def _fetch_daily_5(code: str):
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 주식
        "FID_INPUT_ISCD": code,          # 종목코드 6자리
        "FID_PERIOD_DIV_CODE": "D",      # 일봉
        "FID_ORG_ADJ_PRC": "1",          # 수정주가 반영
    }
    j = request_get(PATH_DAILY, TR_ID_DAILY, params)
    # 응답 키: output, stck_bsop_date(YYYYMMDD), stck_clpr(종가)
    rows = j.get("output", [])
    # 최신이 위에 오는 경우가 많아 최근 5개만 뽑고 날짜 오름차순 정렬
    data = []
    for row in rows[:5][::-1]:
        ymd = row.get("stck_bsop_date", "")
        price = row.get("stck_clpr", "")
        if not ymd or not price:
            continue
        date = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"
        value = float(price)
        data.append({"date": date, "value": value})
    return data

DISPLAY_NAMES = {
    "exchangeRate": "달러 환율(ETF 대체)",
    "kospi": "코스피(ETF 대체)",
    "kosdaq": "코스닥(ETF 대체)",
    "nasdaq": "나스닥(ETF 대체)",
}

def get_indices_payload():
    now = time.time()
    if _STATE["last_payload"] and (now - _STATE["last_at"]) < _CACHE_TTL:
        return _STATE["last_payload"]

    indices = []
    try:
        for k, meta in INDICES.items():
            series = {
                "id": k,
                "name": meta["name"],
                "data": _fetch_daily_5(meta["code"]),
            }
            indices.append(series)
        payload = {"indices": indices}
        _STATE["last_payload"] = payload
        _STATE["last_at"] = now
        return payload

    except Exception as e:
        import traceback
        print("[❌ ERROR get_indices_payload]", e)
        traceback.print_exc()
        if _STATE["last_payload"]:
            return _STATE["last_payload"]
        return {"indices": []}


def get_indices_realtime_payload(request):
    raw_codes = request.query_params.get("codes", "")
    codes = [c.strip() for c in raw_codes.split(",") if c.strip()]
    
    if not codes:
        raise ValueError("Query parameter 'codes' is required.")
    
    results = []

    # "TR_ID" 조회 항목에 맞게 변경
    for code in codes:
        quote = fetch_realtime_quote(REALTIME_TR_ID, code)
        results.append({
            "code": code,
            "quote": quote
        })
    return {"quotes": results}