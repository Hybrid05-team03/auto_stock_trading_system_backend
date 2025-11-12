from typing import Any, Dict, Iterable, List, Union

from kis_prices.client import kis_request

DailyPriceRow = Dict[str, Union[str, float, int]]

def get_daily_price_payload(symbol: str, period: str = "D") -> Dict[str, Any]:
    """
    Call the KIS daily price API and return the raw payload.
    """
    endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    tr_id = "VTTC8814R"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_PERIOD_DIV_CODE": period,
        "FID_ORG_ADJ_PRC": "0",
    }
    res = kis_request("GET", endpoint, tr_id, params=params)
    return res


def get_daily_price(symbol: str, period: str = "D") -> List[Dict]:
    """
    Fetch raw daily price rows from KIS.
    """
    res = get_daily_price_payload(symbol, period=period)
    return res.get("output2", [])


def normalize_daily_prices(data: Iterable[Dict]) -> List[DailyPriceRow]:
    """
    Convert raw KIS daily price rows into normalized dictionaries.
    """
    normalized: List[DailyPriceRow] = []
    for row in data or []:
        try:
            normalized.append(
                {
                    "date": row["stck_bsop_date"],
                    "open": float(row["stck_oprc"]),
                    "high": float(row["stck_hgpr"]),
                    "low": float(row["stck_lwpr"]),
                    "close": float(row["stck_clpr"]),
                    "volume": int(row["acml_vol"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return normalized


def fetch_price_series(symbol: str, period: str = "D") -> List[DailyPriceRow]:
    """
    Helper for REST endpoints that need normalized rows.
    """
    raw = get_daily_price(symbol, period=period)
    return normalize_daily_prices(raw)


def fetch_price_df(symbol: str, period: str = "D"):
    """
    Return normalized rows as a pandas DataFrame.
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to build a DataFrame result.") from exc

    rows = fetch_price_series(symbol, period=period)
    return pd.DataFrame(rows)
