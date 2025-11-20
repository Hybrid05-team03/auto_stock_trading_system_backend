# kis/utils/index_cache.py

import json
from datetime import date
from kis.api.index import kis_get_index_last2
from redis import Redis

r = Redis(decode_responses=True)

def get_cached_yesterday(code: str) -> float | None:
    key = f"index:yesterday:{code}"
    cached = r.get(key)
    today_str = date.today().strftime("%Y%m%d")

    if cached:
        try:
            obj = json.loads(cached)
            if obj.get("date") == today_str:
                return obj.get("close")
        except:
            pass

    result = kis_get_index_last2(code)
    yest = result.get("yesterday")
    if isinstance(yest, dict):
        y_close = yest.get("close")
        if y_close is not None:
            r.set(key, json.dumps({"date": today_str, "close": y_close}), ex=60 * 60 * 6)
            return y_close
    return None