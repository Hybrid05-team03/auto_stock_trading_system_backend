import os
import time
import requests

from typing import Any, Dict, Optional

from django.core.cache import cache

BASE_URL = os.getenv("KIS_BASE_URL")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

TTL = 3600

_TOKEN_CACHE: Dict[str, Optional[Any]] = {"access_token": None, "expires_at": 0.0}


## 토큰 발급
def _fetch_token() -> str:
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    access_token = data.get("access_token") or data.get("accessToken")
    expires_in = int(data.get("expires_in", TTL))
    _TOKEN_CACHE["access_token"] = access_token
    _TOKEN_CACHE["expires_at"] = time.time() + expires_in - 60
    return access_token


## 캐시된 토큰 가져오기
def get_token(force_refresh=False):
    token = cache.get("kis_access_token")
    expires_at = cache.get("kis_token_expires_at", 0)
    expired = time.time() > expires_at

    # cache miss: 토큰 발급
    if force_refresh or not token or expired:
        token = _fetch_token()
        cache.set("kis_access_token", token, timeout=TTL)
        cache.set("kis_token_expires_at", _TOKEN_CACHE["expires_at"], timeout=TTL)

    return token