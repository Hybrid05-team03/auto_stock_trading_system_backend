import requests
import os
from django.core.cache import cache


BASE_URL = os.getenv("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

CACHED_TTL = 86400  # 24시간
_WS_KEY_CACHE = {"approval_key": None, "approval_expires_at": 0}

APPROVAL_TTL = 60 * 60 * 12  # 12시간 (승인키는 최대 24시간 유효)


def _fetch_approval_key():
    url = f"{BASE_URL}/oauth2/Approval"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET,
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()

    approval_key = data.get("approval_key")
    if not approval_key:
        raise Exception(f"approval_key 응답 없음: {data}")

    cache.set("kis_approval_key", approval_key, timeout=APPROVAL_TTL)
    return approval_key


## 캐시된 웹소켓 승인 키 가져오기
def get_web_socket_key(force_refresh=False) -> str:
    approval_key = cache.get("kis_approval_key")

    if force_refresh or not approval_key:
        approval_key = _fetch_approval_key()
    return approval_key