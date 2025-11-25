import requests
import os

from kis.auth.kis_token_real import get_token

BASE_URL_REAL = os.getenv("KIS_BASE_URL_REAL")
APP_KEY_REAL = os.getenv("KIS_APP_KEY_REAL")
APP_SECRET_REAL = os.getenv("KIS_APP_SECRET_REAL")

KIS_CUST_TYPE = os.getenv("KIS_CUST_TYPE")

# --------------------------------------------------------------------
# KIS 요청 헤더 생성
# --------------------------------------------------------------------
def get_headers(tr_id: str):
    token = get_token() # 캐시된 토큰 호출
    return {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY_REAL,
        "appsecret": APP_SECRET_REAL,
        "tr_id": tr_id,
        "custtype": KIS_CUST_TYPE,
        "content-type": "application/json",
    }


# --------------------------------------------------------------------
# KIS API GET 요청
# --------------------------------------------------------------------
def request_get(path, tr_id, params):
    url = f"{BASE_URL_REAL}{path}"
    headers = get_headers(tr_id)

    print(f"▶️ KIS GET {url} {params}")
    kis_response = requests.get(url, headers=headers, params=params, timeout=10)

    print(f"⬅️ STATUS {kis_response.status_code}")
    if not kis_response.ok:
        print("Response text:", kis_response.text[:200])
    kis_response.raise_for_status()
    return kis_response.json()


# --------------------------------------------------------------------
# 공통 POST 요청 (주문, 토큰, 승인키 등)
# --------------------------------------------------------------------
def request_post(endpoint: str, tr_id: str, data: dict):
    url = f"{BASE_URL_REAL}{endpoint}"
    headers = get_headers(tr_id)
    try:
        print(f"▶️ KIS POST {url} {data}")
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] POST {url} 실패: {e}")
        if res is not None:
            print("Response:", res.text[:200])
        raise