import os, time, requests

BASE_URL = os.getenv("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

_token_cache = {"access_token": None, "expires_at": 0}

# 토큰 발급
def _fetch_token():
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    access_token = data.get("access_token") or data.get("accessToken")
    expires_in = int(data.get("expires_in", 3600))
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = time.time() + expires_in - 60
    return access_token

# 토큰 호출
def _get_token():
    if not _token_cache["access_token"] or time.time() > _token_cache["expires_at"]:
        return _fetch_token()
    return _token_cache["access_token"]


# API 요청
def kis_get(path, tr_id, params):
    """KIS 공통 GET 호출 (모의환경)"""
    token = _get_token()
    url = f"{BASE_URL}{path}"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "content-type": "application/json",
    }
    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
