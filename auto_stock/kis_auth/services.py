import os
import time
from typing import Any, Dict, Optional

import requests


BASE_URL = os.getenv("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

_TOKEN_CACHE: Dict[str, Optional[Any]] = {"access_token": None, "expires_at": 0.0}


def _fetch_token() -> str:
    """
    Request a fresh access token from the KIS OAuth endpoint.
    """
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
    expires_in = int(data.get("expires_in", 3600))
    _TOKEN_CACHE["access_token"] = access_token
    _TOKEN_CACHE["expires_at"] = time.time() + expires_in - 60
    return access_token


def get_access_token(force_refresh: bool = False) -> str:
    """
    Return a cached access token or refresh if needed/forced.
    """
    expired = time.time() > float(_TOKEN_CACHE.get("expires_at") or 0)
    if force_refresh or not _TOKEN_CACHE.get("access_token") or expired:
        return _fetch_token()
    return _TOKEN_CACHE["access_token"]


def get_access_token_info() -> Dict[str, Any]:
    """
    Expose cache metadata for observability endpoints.
    """
    return {
        "access_token": _TOKEN_CACHE.get("access_token"),
        "expires_at": _TOKEN_CACHE.get("expires_at"),
        "is_expired": time.time() > float(_TOKEN_CACHE.get("expires_at") or 0),
    }


def kis_get(path: str, tr_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience wrapper around GET requests to KIS REST endpoints.
    """
    token = get_access_token()
    url = f"{BASE_URL}{path}"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "content-type": "application/json",
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()
