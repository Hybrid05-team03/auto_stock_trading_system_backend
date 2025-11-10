from kis.apis.utils import kis_request

def get_daily_price(symbol: str, period="D"):
    """
    일봉 데이터 조회
    """
    endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    tr_id = "VTTC8814R"  # 모의계좌
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_PERIOD_DIV_CODE": period,
        "FID_ORG_ADJ_PRC": "0",
    }
    res = kis_request("GET", endpoint, tr_id, params=params)
    return res.get("output2", [])