import logging
import os
from typing import Any, Dict, Optional

import requests

from kis_auth.services import get_access_token

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("KIS_BASE_URL")
APP_KEY = os.getenv("KIS_APP_KEY_REAL") or os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET_REAL") or os.getenv("KIS_APP_SECRET")


def kis_request(
    method: str,
    endpoint: str,
    tr_id: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Generic request helper for KIS REST endpoints that require an auth token.
    """
    if not BASE_URL or not APP_KEY or not APP_SECRET:
        raise RuntimeError("KIS REST credentials are not fully configured.")

    access_token = get_access_token()
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "authorization": f"Bearer {access_token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "content-type": "application/json",
    }

    try:
        response = requests.request(
            method, url, headers=headers, params=params, json=data, timeout=timeout
        )
        response.raise_for_status()
        res_json = response.json()
    except Exception as exc:
        logger.exception("KIS request failed: %s", exc)
        raise

    if res_json.get("rt_cd") == "0":
        return res_json

    logger.error("KIS API error response: %s", res_json)
    raise RuntimeError(f"KIS API error: {res_json}")
