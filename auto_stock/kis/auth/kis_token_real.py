import os, requests, redis, logging

BASE_URL = os.getenv("BASE_URL_REAL")
APP_KEY = os.getenv("APP_KEY_REAL")
APP_SECRET = os.getenv("APP_SECRET_REAL")

TOKEN_KEY_REAL = "kis_access_token_real"
TTL = 21 * 3600   # 21시간 TTL

r = redis.Redis(decode_responses=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


## 토큰 발급
def _fetch_token() -> str:
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    r_resp = requests.post(url, json=payload, timeout=10)
    r_resp.raise_for_status()
    data = r_resp.json()

    token_real = data.get("access_token") or data.get("accessToken")

    # Redis 캐싱 만료 (TTL=21시간)
    r.set(TOKEN_KEY_REAL, token_real, ex=TTL)
    logger.info("[TOKEN] KIS 실전 토큰 신규 발급 ")

    return token_real


## 캐시된 토큰 가져오기
def get_token():
    token_real = r.get(TOKEN_KEY_REAL)

    if token_real:
        logger.info("[TOKEN] 캐싱된 KIS 실전 토큰 사용")
        return token_real

    return _fetch_token()