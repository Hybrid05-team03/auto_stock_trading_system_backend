import os, time, json, redis, logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def publish_subscription_request(tr_id: str, tr_key: str, sub_type: str):
    payload = {
        "action": "subscribe",
        "tr_id": tr_id,
        "tr_key": tr_key,
        "type": sub_type
    }
    logger.debug(f"[SUB] 구독 요청 → {payload}")
    r.publish("subscribe.add", json.dumps(payload))


def subscribe_and_get_data(tr_id: str, tr_key: str, redis_prefix: str, timeout=10):
    redis_key = f"{redis_prefix}:{tr_key}"
    logger.debug(f"[SUB] redis 구독 저장 → {redis_key}")

    # 1. 기존 데이터 우선 확인
    cached = r.get(redis_key)
    if cached:
        try:
            logger.debug(f"[SUB] redis 구독 저장 → {cached}")
            return json.loads(cached)
        except json.JSONDecodeError:
            logger.warning(f"[ERROR] 캐시된 데이터가 유효한 JSON이 아닙니다: {cached}")
            pass

    # 2. WebSocket 구독 요청
    logger.info(f"[SUB_REQ] 새 데이터 구독 요청 시작: {redis_key}")
    publish_subscription_request(tr_id, tr_key, redis_prefix)

    # 3. Redis에서 데이터 기다리기
    start = time.time() 
    while time.time() - start < timeout:
        val = r.get(redis_key)
        if val:
            try:
                data = json.loads(val)
                elapsed = round(time.time() - start, 2)
                logger.debug(f"[RECEIVE] 데이터 수신 성공 ({elapsed}초 대기) → {val}")
                return data
            except json.JSONDecodeError:
                logger.warning(f"[ERROR] 데이터가 유효한 JSON이 아닙니다: {val}")
                pass
        time.sleep(0.2)
    logger.warning(f"[TIMEOUT] 데이터를 찾지 못하고 종료됨: {redis_key}")
    return None


def get_cached_data(tr_key: str, redis_prefix: str):
    """
    구독 요청 없이 Redis에 캐시된 데이터만 조회
    """
    redis_key = f"{redis_prefix}:{tr_key}"
    cached = r.get(redis_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass
    return None