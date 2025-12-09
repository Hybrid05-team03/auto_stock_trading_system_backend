import os, requests, redis, logging

BASE_URL = os.getenv("BASE_URL")
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")

HTS_ID_KEY = "kis_hts_id_key"
TTL = 23 * 3600   # 23시간 TTL

r = redis.Redis(decode_responses=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _fetch_hts_id_key() -> str:
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    r_resp = requests.post(url, json=payload, timeout=10)
    r_resp.raise_for_status()
    data = r_resp.json()

    ## hts_id key 추출
    # 응답 필드 확인
    hts_id_key = data.get("hts_id") or data.get("htsId") or data.get("hts-id")

    if not hts_id_key:
        logger.error(f"[HTS-ID] 응답에 HTS ID가 없습니다. data={data}")
        return None

    # Redis 캐싱 (TTL=23시간)
    r.set(HTS_ID_KEY, hts_id_key, ex=TTL)
    logger.info("[TOKEN] KIS 모의 HTS ID KEY 발급")

    return hts_id_key


def get_hts_id_key() -> str:
    token = r.get(HTS_ID_KEY)

    if token:
        logger.info("[TOKEN] 캐싱된 KIS 모의 HTS ID KEY 사용")
        return token

    # 캐시 없으면 자동 새 발급
    return _fetch_hts_id_key()