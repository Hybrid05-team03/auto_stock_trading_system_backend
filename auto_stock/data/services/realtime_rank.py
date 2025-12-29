from kis.api.rank import fetch_top10_symbols
# Top 10 Payload
def get_popular_rank_payload() -> dict:
    try:
        rank_data = fetch_top10_symbols(10)
        return {"rank": rank_data} if rank_data else {"rank": []}
    except Exception:
        return {"rank": []}