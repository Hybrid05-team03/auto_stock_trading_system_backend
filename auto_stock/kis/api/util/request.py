import requests
import os

from kis.auth.kis_token import get_token

BASE_URL = os.getenv("KIS_BASE_URL")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

# --------------------------------------------------------------------
# KIS 요청 헤더 생성
# --------------------------------------------------------------------
def _get_headers(tr_id: str):
    token = get_token() # 캐시된 토큰 호출
    return {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
        "content-type": "application/json; charset=utf-8",
    }


# --------------------------------------------------------------------
# KIS API GET 요청
# --------------------------------------------------------------------
def request_get(path, tr_id, params):
    url = f"{BASE_URL}{path}"
    headers = _get_headers(tr_id)

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
    url = f"{BASE_URL}{endpoint}"
    headers = _get_headers(tr_id)
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