import os, time, json, redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def publish_subscription_request(tr_id: str, tr_key: str, sub_type: str):
    r.publish("subscribe.add", json.dumps({
        "action": "subscribe",
        "tr_id": tr_id,
        "tr_key": tr_key,
        "type": sub_type
    }))


def subscribe_and_get_data(tr_id: str, tr_key: str, redis_prefix: str, timeout=10):
    redis_key = f"{redis_prefix}:{tr_key}"

    # 1. 기존 데이터 우선 확인
    cached = r.get(redis_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass

    # 2. WebSocket 구독 요청
    publish_subscription_request(tr_id, tr_key, redis_prefix)

    # 3. Redis에서 데이터 기다리기
    start = time.time()
    while time.time() - start < timeout:
        val = r.get(redis_key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        time.sleep(0.2)

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