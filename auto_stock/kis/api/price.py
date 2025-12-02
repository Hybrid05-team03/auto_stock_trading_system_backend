import os
import logging
import redis
import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Union

from kis.api.util.request import request_get

logger = logging.getLogger(__name__)
r = redis.Redis(decode_responses=True)  # Redis 연결 (기본)

DailyPriceRow = Dict[str, Union[str, float, int]]


# --------------------------------------------------------------------
# 일별 시세 조회 (REST API)
# --------------------------------------------------------------------
def fetch_price_series(symbol: str, period: str = "D") -> List[DailyPriceRow]:
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = os.getenv("PRICE_DAILY_TR_ID")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 주식시장 구분코드 (J: 주식)
        "FID_INPUT_ISCD": symbol,         # 종목코드 (예: 005930)
        "FID_PERIOD_DIV_CODE": period,    # D:일, W:주, M:월
        "FID_ORG_ADJ_PRC": "0",           # 수정주가 반영여부
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

    print("[DEBUG]", data.keys(), "rt_cd:", data.get("rt_cd"), "msg_cd:", data.get("msg_cd"), "msg1:", data.get("msg1"))
    return result


# --------------------------------------------------------------------
# 단일 시세 (현재가) 조회 (REST API)
# --------------------------------------------------------------------
def kis_get_realtime_price(symbol: str) -> float:
    """
    Get the latest realtime price for a symbol using REST (real account version).
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = os.getenv("PRICE_TR_ID")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 시장코드
        "FID_INPUT_ISCD": symbol,         # 종목코드
    }

    try:
        data = request_get(path, tr_id, params)
        output = data.get("output", {})
        price = output.get("stck_prpr")
        return float(price) if price else np.nan
    except Exception as e:
        logger.error(f"[REST ERROR] {symbol}: {e}")
        return np.nan


## 전일 종가 조회
def fetch_yesterday_close(code: str) -> float | None:
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
    tr_id = os.getenv("DOMESTIC_INDEX_DAILY_TR_ID")

    today_d = date.today()
    start_d = today_d - timedelta(days=10)

    params = {
        "FID_COND_MRKT_DIV_CODE": "U",  # 업종
        "FID_INPUT_ISCD": code,
        "FID_INPUT_DATE_1": start_d.strftime("%Y%m%d"),
        "FID_INPUT_DATE_2": today_d.strftime("%Y%m%d"),
        "FID_PERIOD_DIV_CODE": "D",
    }

    try:
        data = request_get(path, tr_id, params)
    except Exception as e:
        logger.error(f"[KIS INDEX ERROR] Failed to fetch index {code}: {e}")
        return None

    rows = data.get("output2") or []
    if len(rows) < 2:
        logger.warning(f"[KIS INDEX] Not enough data for code={code}")
        return None

    try:
        # 최신 전일 종가 = 두 번째 마지막 데이터
        yest_row = sorted(rows, key=lambda r: r["stck_bsop_date"])[-2]
        return float(yest_row["bstp_nmix_prpr"])
    except Exception as e:
        logger.warning(f"[KIS INDEX] Failed to parse yesterday price for {code}: {e}")
        return None


# --------------------------------------------------------------------
# 지수 전일 종가 Redis 캐싱 래퍼
# --------------------------------------------------------------------
def get_or_set_index_yesterday(code: str) -> float | None:
    redis_key = f"index:yesterday:{code}"
    cached = r.get(redis_key)
    if cached:
        try:
            return float(cached)
        except Exception:
            r.delete(redis_key)

    # 코드 종류에 따라 API 방식 분기
    if code == "261240":
        # 환율은 '주식형 ETF' API 사용
        series = fetch_price_series(code)
        yesterday_price = series[0]["close"] if series else None
    else:
        # 지수는 지수 전용 API 사용
        yesterday_price = fetch_yesterday_close(code)

    if yesterday_price is not None:
        r.set(redis_key, yesterday_price, ex=60 * 60 * 12)

    return yesterday_price