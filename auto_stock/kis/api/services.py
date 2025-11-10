from kis.apis.quote import get_daily_price
import pandas as pd

def fetch_price_df(symbol: str) -> pd.DataFrame:
    data = get_daily_price(symbol)
    df = pd.DataFrame([
        {
            "date": d["stck_bsop_date"],
            "open": float(d["stck_oprc"]),
            "high": float(d["stck_hgpr"]),
            "low": float(d["stck_lwpr"]),
            "close": float(d["stck_clpr"]),
            "volume": int(d["acml_vol"]),
        } for d in data
    ])
    return df