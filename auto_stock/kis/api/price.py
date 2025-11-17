import logging
import os
from datetime import date, timedelta, timezone
from typing import List, Dict, Union, Any, Optional

import numpy as np

from kis.api.util.request import request_get

logger = logging.getLogger(__name__)

DailyPriceRow = Dict[str, Union[str, float, int]]

# 업종코드 → 업종명 매핑 (필요하면 계속 추가)
INDEX_CODE_NAME_MAP = {
    "0001": "코스피 종합",
    "1001": "코스닥",
    "6295": "NASDAQ-100 TR",
    "6001": "미국달러선물",
}

KST = timezone(timedelta(hours=9))

# --------------------------------------------------------------------
# 개별 종목 일별 시세 조회 (기존 기능)
# --------------------------------------------------------------------
def fetch_price_series(symbol: str, period: str = "D") -> List[DailyPriceRow]:
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 주식시장 구분코드 (J: 주식)
        "FID_INPUT_ISCD": symbol,        # 종목코드 (예: 005930)
        "FID_PERIOD_DIV_CODE": period,   # D:일, W:주, M:월
        "FID_ORG_ADJ_PRC": "0",          # 수정주가 반영여부
    }

    try:
        data = request_get(path, tr_id, params)
        raw = data.get("output", [])
    except Exception as e:
        logger.error(f"[KIS ERROR] Failed to fetch {symbol}: {e}")
        return []

    result: List[DailyPriceRow] = []
    for row in raw or []:
        try:
            result.append({
                "date": row["stck_bsop_date"],
                "open": float(row["stck_oprc"]),
                "high": float(row["stck_hgpr"]),
                "low": float(row["stck_lwpr"]),
                "close": float(row["stck_clpr"]),
                "volume": int(row["acml_vol"]),
            })
        except (KeyError, TypeError, ValueError):
            continue

    print(
        "[DEBUG]",
        "from price.py",
        data.keys(),
        "rt_cd:", data.get("rt_cd"),
        "msg_cd:", data.get("msg_cd"),
        "msg1:", data.get("msg1"),
    )
    return result


# --------------------------------------------------------------------
# 개별 종목 단일 현재가 조회 (REST, 기존 기능)
# --------------------------------------------------------------------
def kis_get_realtime_price(symbol: str) -> float:
    """
    Get the latest realtime price for a symbol using REST (real account version).
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 시장코드
        "FID_INPUT_ISCD": symbol,        # 종목코드
    }

    try:
        data = request_get(path, tr_id, params)
        output = data.get("output", {})
        price = output.get("stck_prpr")
        return float(price) if price else np.nan
    except Exception as e:
        logger.error(f"[REST ERROR] {symbol}: {e}")
        return np.nan

######################################################################
## Index(국내 지수) 최근 2일 호출 
def kis_get_index_last2(code: str) -> Dict[str, Any]:
    path = os.getenv("KIS_INDEX_DAILY_URL")  # /uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice
    tr_id = os.getenv("KIS_INDEX_DAILY_TR_ID", "FHKUP03500100")

    today_d = date.today()
    start_d = today_d - timedelta(days=10)   # 주말/공휴일 감안해서 10일

    params = {
        "FID_COND_MRKT_DIV_CODE": "U",                         # 업종: U
        "FID_INPUT_ISCD": code,                                # 업종 상세코드 (예: 0001코스피, 1001코스닥 등)
        "FID_INPUT_DATE_1": start_d.strftime("%Y%m%d"),        # 조회 시작일자
        "FID_INPUT_DATE_2": today_d.strftime("%Y%m%d"),        # 조회 종료일자
        "FID_PERIOD_DIV_CODE": "D",                            # 일봉
    }

    try:
        data = request_get(path, tr_id, params)
    except Exception as e:
        logger.error(f"[KIS INDEX ERROR] Failed to fetch index {code}: {e}")
        return {
            "name": INDEX_CODE_NAME_MAP.get(code),
            "today": None,
            "yesterday": None,
        }

    print(
        "[INDEX DEBUG] rt_cd:", data.get("rt_cd"),
        "msg_cd:", data.get("msg_cd"),
        "msg1:", data.get("msg1"),
        "keys:", list(data.keys())
    )

    output1 = data.get("output1") or {}
    rows = data.get("output2") or []

    if not rows:
        logger.warning(f"[KIS INDEX] No output2 rows for code={code}")
        return {
            "name": output1.get("hts_kor_isnm") or INDEX_CODE_NAME_MAP.get(code),
            "today": None,
            "yesterday": None,
        }

    # output2 예시:
    # {
    #   "stck_bsop_date": "20251117",
    #   "bstp_nmix_prpr": "2500.12",
    #   ...
    # }
    parsed = []
    for row in rows:
        ymd = row.get("stck_bsop_date")
        price_str = row.get("bstp_nmix_prpr")  # 업종 지수 현재가 (종가처럼 씀)
        if not ymd or not price_str:
            continue
        try:
            close = float(price_str)
        except (ValueError, TypeError):
            continue
        parsed.append({"date": ymd, "close": close})

    if not parsed:
        logger.warning(f"[KIS INDEX] Parsed rows empty for code={code}")
        return {
            "name": output1.get("hts_kor_isnm") or INDEX_CODE_NAME_MAP.get(code),
            "today": None,
            "yesterday": None,
        }

    # 날짜 기준 오름차순 정렬
    parsed.sort(key=lambda r: r["date"])

    today_row = parsed[-1]
    yest_row = parsed[-2] if len(parsed) >= 2 else None

    name = output1.get("hts_kor_isnm") or INDEX_CODE_NAME_MAP.get(code)

    result: Dict[str, Any] = {
        "name": name,
        "today": [
            today_row["date"],
            today_row["close"],
        ],
        "yesterday": (
            [yest_row["date"], yest_row["close"]]
            if yest_row
            else None
        ),
    }
    print("[INDEX DEBUG] kis_get_index_last2 result:", result)
    return result
