import requests
import os
import time

from django.core.cache import cache

CACHED_TTL = 86400  # 24시간
_WS_KEY_CACHE = {"approval_key": None, "approval_expires_at": 0}


def _get_env():
    BASE_URL = os.getenv("KIS_BASE_URL")
    APP_KEY = os.getenv("KIS_APP_KEY")
    APP_SECRET = os.getenv("KIS_APP_SECRET")

    if not all([BASE_URL, APP_KEY, APP_SECRET]):
        raise EnvironmentError(
            "KIS 환경변수(KIS_BASE_URL, KIS_APP_KEY, KIS_APP_SECRET)가 설정되지 않았습니다."
        )
    return BASE_URL, APP_KEY, APP_SECRET


## key, secret 확인
def _ensure_kis_credentials():
    BASE_URL, APP_KEY, APP_SECRET = _get_env()
    if not all([BASE_URL, APP_KEY, APP_SECRET]):
        raise EnvironmentError("KIS 환경변수(KIS_BASE_URL, KIS_APP_KEY, KIS_APP_SECRET)가 설정되지 않았습니다.")


## 웹소켓 승인 키 발급 요청
def _fetch_web_socket_key() -> str:
    BASE_URL, APP_KEY, APP_SECRET = _get_env()
    _ensure_kis_credentials()

    url = f"{BASE_URL}/oauth2/Approval"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET,
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()

    approval_key = data.get("approval_key") or data.get("approvalKey")
    expires_in = int(data.get("expires_in", CACHED_TTL))

    _WS_KEY_CACHE["approval_key"] = approval_key
    _WS_KEY_CACHE["expires_at"] = time.time() + expires_in - 60  # 만료 1분 전까지 유효

    return approval_key


## 캐시된 웹소켓 승인 키 가져오기
def get_web_socket_key(force_refresh=False) -> str:
    socket_key = cache.get("kis_socket_key")
    expires_at = cache.get("kis_socket_expires_at", 0)
    expired = time.time() > expires_at

    if force_refresh or not socket_key or expired:
        socket_key = _fetch_web_socket_key()
        cache.set("kis_socket_key", socket_key, timeout=CACHED_TTL)
        cache.set("kis_socket_expires_at", _WS_KEY_CACHE["expires_at"], timeout=CACHED_TTL)

    return socket_key