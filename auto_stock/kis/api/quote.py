import os
import requests
import pandas as pd
from .auth import _get_headers

BASE_URL = os.getenv("KIS_BASE_URL")

### KIS API 시세 조회 요청
def _fetch_kis_data(tr_id: str, endpoint: str, params: dict, count: int = 100) -> pd.DataFrame:

    headers = _get_headers(tr_id=tr_id)
    url = f"{BASE_URL}/{endpoint}"

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        output = data.get("output2") or data.get("output")

        if not output:
            raise ValueError(f"KIS API invalid response: {data}")

        df = pd.DataFrame(output[:count][::-1])
        return df

    except Exception as e:
        print(f"[ERROR] KIS FETCH {tr_id} {e}")
        return pd.DataFrame()

### 일자 별 주식 현재가
# https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-daily-price
def get_daily_price(symbol: str, count: int = 100) -> pd.DataFrame:
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,    # 종목 코드
        "FID_PERIOD_DIV_CODE": "D",  # D: 최근 거래 30일
        "FID_ORG_ADJ_PRC": "1",      # 1: 수정주가 반영
    }

    # KIS API 요청
    df = _fetch_kis_data(
        tr_id="FHKST01010400",
        endpoint="uapi/domestic-stock/v1/quotations/inquire-daily-price",
        params=params,
        count=count,
    )

    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    df.rename(columns={
        "stck_bsop_date": "date",
        "stck_oprc": "open",
        "stck_hgpr": "high",
        "stck_lwpr": "low",
        "stck_clpr": "close",
        "acml_vol": "volume",
    }, inplace=True)

    df["date"] = pd.to_datetime(df["date"])
    df = df.astype(float, errors="ignore")

    return df[["date", "open", "high", "low", "close", "volume"]]