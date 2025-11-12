import logging
import os
import time
from typing import Dict, List

from kis_auth.services import kis_get
from kis_prices.services import normalize_daily_prices
from kis_realtime.services import fetch_realtime_quotes

from .symbols import INDICES

logger = logging.getLogger(__name__)

# Cache for the last REST payload so the indices endpoint stays responsive.
_CACHE_TTL = int(os.getenv("INDICES_CACHE_TTL_SECONDS", "5"))
_STATE = {"last_payload": None, "last_at": 0.0}

# Daily ETF-based indices configuration.
TR_ID_DAILY = "FHKST01010400"
PATH_DAILY = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"


def _fetch_daily_5(code: str) -> List[Dict[str, float]]:
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "1",
    }
    response = kis_get(PATH_DAILY, TR_ID_DAILY, params)
    rows = normalize_daily_prices(response.get("output", []))
    data = []
    for row in rows[:5][::-1]:
        ymd = row.get("date", "")
        price = row.get("close")
        if not ymd or price is None:
            continue
        date = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"
        data.append({"date": date, "value": float(price)})
    return data


def get_indices_payload() -> Dict[str, List[Dict[str, float]]]:
    now = time.time()
    if _STATE["last_payload"] and (now - _STATE["last_at"]) < _CACHE_TTL:
        return _STATE["last_payload"]

    indices = []
    try:
        for key, meta in INDICES.items():
            series = {
                "id": key,
                "name": meta["name"],
                "data": _fetch_daily_5(meta["code"]),
            }
            indices.append(series)
        payload = {"indices": indices}
        _STATE["last_payload"] = payload
        _STATE["last_at"] = now
        return payload
    except Exception:
        if _STATE["last_payload"]:
            logger.exception("Returning cached indices payload due to failure.")
            return _STATE["last_payload"]
        logger.exception("Unable to build indices payload.")
        return {"indices": []}


def get_indices_realtime_payload():
    quotes = fetch_realtime_quotes(INDICES)
    return {"quotes": quotes}
