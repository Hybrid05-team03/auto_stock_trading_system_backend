import requests
import logging
import os
from kis.apis.auth import get_access_token

logger = logging.getLogger(__name__)

def kis_request(method: str, endpoint: str, tr_id: str, params=None, data=None):
    """
    한국투자증권 API 공통 호출 함수
    """
    base_url = os.getenv("KIS_BASE_URL")
    appkey = os.getenv("KIS_APP_KEY_REAL")
    appsecret = os.getenv("KIS_APP_SECRET_REAL")

    access_token = get_access_token()

    url = f"{base_url}{endpoint}"

    headers = {
        "authorization": f"Bearer {access_token}",
        "appkey": appkey,
        "appsecret": appsecret,
        "tr_id": tr_id,
        "content-type": "application/json",
    }

    try:
        response = requests.request(method, url, headers=headers, params=params, json=data)
        res_json = response.json()

        if res_json.get("rt_cd") == "0":
            return res_json
        else:
            logger.error(f"KIS API Error: {res_json}")
            raise Exception(f"KIS API Error: {res_json}")

    except Exception as e:
        logger.exception(f"KIS Request Failed: {e}")
        raise