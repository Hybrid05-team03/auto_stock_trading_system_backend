import os, logging
import numpy as np
import pandas as pd

from kis.api.util.request_real import request_get

logger = logging.getLogger(__name__)


def kis_get_last_quote(symbol: str, count: int = 100) -> pd.DataFrame:
    """
    REST: 과거 일봉 조회
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = os.getenv("PRICE_DAILY_TR_ID")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "1",
    }

    res = request_get(path, tr_id, params)
    output = res.get("output", [])

    df = pd.DataFrame(output)
    if df.empty:
        return df

    df["close"] = df["stck_clpr"].astype(float)
    df["date"] = pd.to_datetime(df["stck_bsop_date"])
    return df[["date", "close"]].tail(count)


def kis_get_price_rest(symbol: str) -> float:
    """
    REST: 단일 현재가 조회 (WS 실패 시 backup)
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = os.getenv("PRICE_TR_ID")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
    }

    try:
        res = request_get(path, tr_id, params)
        price = res.get("output", {}).get("stck_prpr")
        return float(price) if price else np.nan
    except:
        return np.nan


## 시가 총액 조회
def kis_get_market_cap(symbol: str) -> float:
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = os.getenv("PRICE_TR_ID")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
    }

    try:
        res = request_get(path, tr_id, params)
        price = res.get("output", {}).get("hts_avls")
        return float(price) if price else np.nan
    except:
        return np.nan