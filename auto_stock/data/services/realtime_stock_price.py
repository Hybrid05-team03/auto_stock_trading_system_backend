import os
from kis.websocket.util.kis_data_save import subscribe_and_get_data, get_cached_data
from kis.data.search_code import mapping_code_to_name
from kis.api.quote import kis_get_price_snapshot
from kis.api.util.market_time import is_after_market_close

# Stock price Payload
def get_realtime_stock_payload(codes: list) -> dict:
    tr_id = os.getenv("PRICE_REALTIME_TR_ID")
    results = []
    is_market_open = is_after_market_close()

    for code in codes:
        # 데이터 수집 (WebSocket/Redis 캐시)
        snap = kis_get_price_snapshot(code)
        if is_market_open:
            print("[INFO] 실시간 조회")
            data = subscribe_and_get_data(tr_id, code, "price", timeout=3)
        else:
            print("[INFO] 캐싱 데이터 조회")
            data = get_cached_data(code, "price")

        stock_name = mapping_code_to_name(code)
        
        if data:
            print("[INFO] WS 응답")
            results.append({
                "name": stock_name,
                "code": code,
                "currentPrice": str(data.get("current_price", "0")),
                "changePercent": str(data.get("change_rate", "0")),
                "volume": str(data.get("trade_value", "0")),
                "price": str(snap["market_cap"]),
            })
        else:
            print("[INFO] 캐싱 데이터 없음")
            print("[INFO] REST 응답")
            # REST Fallback
            price = snap.get("price")
            results.append({
                "name": stock_name,
                "code": code,
                "currentPrice": str(snap["price"]),
                "changePercent": str(snap["change_rate"]),
                "volume": str(snap["volume"]),
                "price": str(snap["market_cap"]),
            })

    return results