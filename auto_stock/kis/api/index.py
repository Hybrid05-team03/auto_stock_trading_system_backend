import os
import logging
from datetime import date, timedelta

from kis.api.util.request import request_get

logger = logging.getLogger(__name__)

# 업종코드 → 업종명 매핑 (필요하면 계속 추가)
INDEX_CODE_NAME_MAP = {
    "0001": "코스피 종합",
    "1001": "코스닥",
    "6295": "NASDAQ-100 TR",
    "6001": "미국달러선물",
}


def kis_get_index_last2(code: str) -> dict:
    path = os.getenv("KIS_BASE_URL")
    tr_id = os.getenv("KIS_INDEX_DAILY_TR_ID", "FHKUP03500100")

    today_d = date.today()
    start_d = today_d - timedelta(days=10)

    params = {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_d.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": today_d.strftime("%Y%m%d"),
        "FID_PERIOD_DIV_CODE": "D",
    }

    try:
        data = request_get(path, tr_id, params)
    except Exception as e:
        logger.error(f"[KIS INDEX ERROR] Failed to fetch index {code}: {e}")
        return {"today": None, "yesterday": None}

    rows = data.get("output2", [])
    if not rows:
        return {"today": None, "yesterday": None}

    parsed = []
    for row in rows:
        ymd = row.get("stck_bsop_date")
        price_str = row.get("bstp_nmix_prpr")
        if not ymd or not price_str:
            continue
        try:
            close = float(price_str)
            parsed.append({"date": ymd, "close": close})
        except:
            continue

    if len(parsed) < 2:
        return {"today": None, "yesterday": None}

    parsed.sort(key=lambda r: r["date"])
    return {
        "today": parsed[-1],
        "yesterday": parsed[-2]
    }