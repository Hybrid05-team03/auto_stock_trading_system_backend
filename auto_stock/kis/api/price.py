import logging
import numpy as np
from typing import List, Dict, Union

from kis.api.util.request import request_get

logger = logging.getLogger(__name__)

DailyPriceRow = Dict[str, Union[str, float, int]]

# --------------------------------------------------------------------
# 일별 시세 조회
# --------------------------------------------------------------------
def fetch_price_series(symbol: str, period: str = "D") -> List[DailyPriceRow]:
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"
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
# 단일 시세 (현재가) 조회
# --------------------------------------------------------------------
def kis_get_realtime_price(symbol: str) -> float:
    """
    Get the latest realtime price for a symbol using REST (real account version).
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
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