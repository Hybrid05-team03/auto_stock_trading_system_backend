import pandas as pd

from kis.api.util.request import request_get

def get_daily_price(symbol: str, period="D"):
    """
    일봉 데이터 조회
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    tr_id = "VTTC8814R"
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_PERIOD_DIV_CODE": period,
        "FID_ORG_ADJ_PRC": "0",
    }
    res = request_get(path, tr_id, params=params)
    return res.get("output2", [])


from kis.websocket.util.request_ws import request_quota_data

# --------------------------------------------------------------------
# 과거 일자별 시세 조회 : 특정 종목(symbol)의 최근 N일 간의 종가·고가·저가·거래량 조회
# --------------------------------------------------------------------
def kis_get_last_quota(symbol: str, count: int = 100) -> pd.DataFrame:
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # 주식
        "FID_INPUT_ISCD": symbol,        # 종목 코드
        "FID_PERIOD_DIV_CODE": "D",      # D: 최근 거래 30일
        "FID_ORG_ADJ_PRC": "1",          # 1: 수정주가 반영
    }

    # count 필요
    df = request_get("uapi/domestic-stock/v1/quotations/inquire-daily-price", "FHKST01010400", params)

    if df.empty:
        print(f"[WARN] {symbol}: 과거 시세 데이터 없음")
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    # 컬럼명 변환
    df.rename(columns={"stck_bsop_date": "date", "stck_oprc": "open", "stck_hgpr": "high",
        "stck_lwpr": "low", "stck_clpr": "close", "acml_vol": "volume"}, inplace=True)

    # 데이터 변환
    df["date"] = pd.to_datetime(df["date"])
    df = df.astype(float, errors="ignore")

    return df[["date", "open", "high", "low", "close", "volume"]]