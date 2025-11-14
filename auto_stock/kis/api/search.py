import os
from kis.api.util.request import request_get

# 검색할 종목명
query = "삼성전자"
TR_ID = os.getenv("KIS_SEARCH_TR_ID") # 모의 계좌 미지원
endpoint = "/uapi/domestic-stock/v1/quotations/search-stock-info"

# 요청 파라미터
params = {
    "PRDT_TYPE_CD": "300",   # 주식상품유형 (300: 주식)
    "PDNO": "",              # 종목코드 (빈칸이면 이름으로 검색)
    "PDNM": query            # 종목명
}

# 요청
response = request_get(endpoint, tr_id=TR_ID, params=params)

# 결과 출력
if response.status_code == 200:
    data = response.json()
    if "output" in data and len(data["output"]) > 0:
        for stock in data["output"]:
            print(f"종목명: {stock['prdt_name']} / 종목코드: {stock['pdno']}")
    else:
        print("검색 결과가 없습니다.")
else:
    print("API 요청 실패:", response.status_code, response.text)