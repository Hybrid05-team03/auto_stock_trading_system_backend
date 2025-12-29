import os
import logging

from kis.api.price import get_or_set_index_yesterday
from kis.api.index import (
    fetch_domestic_index_snapshot,
    fetch_overseas_index_snapshot,
)
from kis.websocket.util.kis_data_save import (
    subscribe_and_get_data,
    get_cached_data,
)
from kis.constants.const_index import (
    INDEX_CODE_NAME_MAP,
    OVERSEAS_INDEX_CODE_NAME_MAP,
)
from kis.api.util.market_time import is_after_market_close

logger = logging.getLogger(__name__)

# Index Payload
def get_realtime_index_payload() -> dict:
    tr_id = os.getenv("INDEX_REALTIME_TR_ID")
    results = []

    # True = 장중, False = 장마감
    is_market_open = is_after_market_close()

    # --------------------------------------------------
    # 1) 국내 지수 (코스피 / 코스닥)
    # --------------------------------------------------
    for code, name in INDEX_CODE_NAME_MAP.items():
        yesterday = get_or_set_index_yesterday(code)

        if is_market_open:
            ws_data = subscribe_and_get_data(tr_id, code, "index", timeout=3)
        else:
            ws_data = get_cached_data(code, "index")

        if ws_data and ws_data.get("price"):
            results.append({
                "name": name,
                "yesterday": yesterday,
                "today": ws_data["price"],
            })
        else:
            # REST fallback
            snap = fetch_domestic_index_snapshot(code)
            if snap:
                results.append({
                    "name": snap["name"],
                    "yesterday": snap.get("yesterday"),
                    "today": snap["today"],
                })

    # --------------------------------------------------
    # 2) 해외 지수 (달러환율 / 나스닥100)
    # --------------------------------------------------
    for index_key in OVERSEAS_INDEX_CODE_NAME_MAP.keys():
        snap = fetch_overseas_index_snapshot(index_key)
        if snap:
            results.append({
                "name": snap["name"],
                "yesterday": snap.get("yesterday"),
                "today": snap["today"],
            })

    return {"indices": results} if results else {"indices": []}
