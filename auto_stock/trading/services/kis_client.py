import requests
import os

BASE_URL = os.getenv("KIS_BASE_URL")
APP_KEY = os.getenv("KIS_APP_KEY_PAPER")
APP_SECRET = os.getenv("KIS_APP_SECRET_PAPER")

def get_access_token():

    url = f"{BASE_URL}/oauth2/tokenP"
    data = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    res = requests.post(url, data=data)
    token_data = res.json()

    if "access_token" not in token_data:
        raise Exception(f"Token 발급 실패: {token_data}")

    access_token = token_data["access_token"]

    # 새 토큰을 .env 대신 메모리 변수나 캐시로 관리 (임시로 env에 넣어도 됨)
    print("✅ 새 Access Token 발급 완료:", access_token)
    return access_token


def get_price_data(symbol: str, period: str = "D") -> list[dict]:
    ACCESS_TOKEN = get_access_token()

    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"

    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "VTTC8814R",   # ⚠️ 모의계좌용 TR ID
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",   # 주식시장 (정상)
        "FID_INPUT_ISCD": symbol,        # 반드시 6자리 숫자만
        "FID_PERIOD_DIV_CODE": period,   # D(일봉)
        "FID_ORG_ADJ_PRC": "1",          # 수정주가 반영
    }

    res = requests.get(url, headers=headers, params=params)
    print(res.status_code, res.text)
    data = res.json()

    if "output2" not in data:
        raise Exception(f"API response error: {data}")

    rows = data["output2"]
    return [
        {
            "date": r["stck_bsop_date"],
            "open": float(r["stck_oprc"]),
            "high": float(r["stck_hgpr"]),
            "low": float(r["stck_lwpr"]),
            "close": float(r["stck_clpr"]),
            "volume": int(r["acml_vol"]),
        }
        for r in rows
    ]