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


def kis_get_price_snapshot(symbol: str) -> dict:
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = os.getenv("PRICE_TR_ID")

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
    }

    try:
        res = request_get(path, tr_id, params)
        output = res.get("output", {})

        def _f(v):
            try:
                return float(v)
            except:
                return np.nan

        return {
            "price": _f(output.get("stck_prpr")),
            "market_cap": _f(output.get("hts_avls")),
            "volume": _f(output.get("acml_vol")),
            "change": _f(output.get("prdy_vrss")),
            "change_rate": _f(output.get("prdy_ctrt")),
        }

    except Exception as e:
        logger.warning(f"[KIS] price snapshot failed ({symbol}): {e}")
        return {}
