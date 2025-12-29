import os, requests, redis, logging

BASE_URL = os.getenv("BASE_URL")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")

TOKEN_KEY = "kis_access_token"
TTL = 21 * 3600   # 21시간 TTL

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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

    token = data.get("access_token") or data.get("accessToken")

    # Redis 캐싱 (TTL=21시간)
    r.set(TOKEN_KEY, token, ex=TTL)
    logger.info("[TOKEN] KIS 모의 토큰 신규 발급")

    return token


def get_token() -> str:
    token = r.get(TOKEN_KEY)

    if token:
        logger.info("[TOKEN] 캐싱된 KIS 모의 토큰 사용")
        return token

    # 캐시 없으면 자동 새 발급
    return _fetch_token()