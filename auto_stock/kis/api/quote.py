import numpy as np
import pandas as pd
from kis.api.util.request import request_get

def kis_get_last_quote(symbol: str, count: int = 100) -> pd.DataFrame:
    """
    REST: 과거 일봉 조회
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"
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
    tr_id = "FHKST01010100"
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