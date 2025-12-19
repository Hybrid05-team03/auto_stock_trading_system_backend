import os
from kis.websocket.util.kis_data_save import subscribe_and_get_data, get_cached_data
from kis.data.search_code import mapping_code_to_name
from kis.api.quote import kis_get_market_cap, kis_get_price_rest
from kis.api.util.market_time import is_after_market_close

# Stock price Payload
def get_realtime_stock_payload(codes: list) -> dict:
    tr_id = os.getenv("PRICE_REALTIME_TR_ID")
    results = []
    is_market_open = is_after_market_close()

    for code in codes:
        # 데이터 수집 (WebSocket/Redis 캐시)
        if is_market_open:
            data = subscribe_and_get_data(tr_id, code, "price", timeout=3)
        else:
            data = get_cached_data(code, "price")

        stock_name = mapping_code_to_name(code)
        
        if data:
            results.append({
                "name": stock_name,
                "code": code,
                "currentPrice": data.get("current_price"),
                "changePercent": data.get("change_rate"),
                "volume": data.get("trade_value"),
            })
        else:
            # REST Fallback
            rest_price = kis_get_price_rest(code)
            results.append({
                "name": stock_name,
                "code": code,
                "currentPrice": rest_price if rest_price else 0,
                "changePercent": "0",
                "volume": "0",
            })

    return {"stock": results}