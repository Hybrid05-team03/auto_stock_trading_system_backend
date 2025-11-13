import os
import requests
import pandas as pd

from kis.api.util.request import _get_headers

BASE_URL = os.getenv("KIS_BASE_URL")

# --------------------------------------------------------------------
# 공통 API 호출 함수
# --------------------------------------------------------------------
def request_quota_data(tr_id: str, endpoint: str, params: dict, count: int = 100) -> pd.DataFrame:
    BASE_URL = os.getenv("KIS_BASE_URL")
    headers = _get_headers(tr_id=tr_id)
    url = f"{BASE_URL}/{endpoint}"

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        output = data.get("output2") or data.get("output")

        if not output:
            raise ValueError(f"KIS API invalid response: {data}")

        # output이 dict이면 단일 데이터, list면 시계열 데이터
        if isinstance(output, dict):
            df = pd.DataFrame([output])
        else:
            df = pd.DataFrame(output[:count][::-1])

        return df

    except Exception as e:
        print(f"[ERROR] KIS FETCH {tr_id}: {e}")
        return pd.DataFrame()