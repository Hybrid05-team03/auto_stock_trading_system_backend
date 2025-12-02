import os

from kis.api.util.request_real import request_get


def fetch_top10_symbols(count:int):

    path = "/uapi/domestic-stock/v1/ranking/market-cap"
    tr_id = os.getenv("RANK_TR_ID")
    params = {
        "fid_cond_mrkt_div_code": "J",  # 코스피
        "fid_cond_scr_div_code": "20174",
        "fid_div_cls_code": "1",
        "fid_input_iscd": "0000",
        "fid_trgt_cls_code": "0",
        "fid_trgt_exls_cls_code": "0",
        "fid_input_price_1": "0",
        "fid_input_price_2": "0",
        "fid_vol_cnt": "0"
    }

    data = request_get(path, tr_id, params)
    output = data.get("output", [])
    result = [
        {
            "code": item["mksc_shrn_iscd"],
            "name": item["hts_kor_isnm"]
            # "market_cap": int(item["stck_avls"]) # 시가총액
        }
        for item in output[:count]
    ]

    return result