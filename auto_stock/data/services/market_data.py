from data.services.realtime_index import get_realtime_index_payload
from data.services.realtime_rank import get_popular_rank_payload
from data.services.realtime_stock_price import get_realtime_stock_payload

# Combined Payload
def get_combined_market_payload(stock_codes):
    index_p = get_realtime_index_payload()
    rank_p = get_popular_rank_payload()
    stock_p = get_realtime_stock_payload(stock_codes)

    return {
        "indices": index_p.get("indices", []),
        "rank": rank_p.get("rank", []),
        "stock": stock_p.get("stock", [])
    }