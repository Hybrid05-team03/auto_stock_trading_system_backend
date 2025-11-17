1. 국내지수 조회를 돕기위해 pirce.py에 "INDEX_CODE_NAME_MAP"을 추가했습니다.

2. price.py에 최근 2일 (어제, 오늘) 국내 지수 조회 "kis_get_index_last2"를 추가했습니다.

3. kis_test/views.py에 국내지수 조회 테스트를 위한 IndexView 클래스를 추가했습니다
     - REST 방식(kis_get_index_last2)으로 기본값을 조회합니다.
     - WebSocket 방식으로 시도 -> "성공" -> 오늘 결과값을 websocket 실시간 데이터로 교체합니다.
     - WebSocket은 주식시장이 열려있을 때만 정상적으로 값을 불러올 수 있습니다. 

4. kis_test/urls.py에 국내주식 조회 용 api 주소를 추가했습니다. "index/"
     - 호출 url : http://localhost:8000/api/kis-test/index/?codes=0001,1001,6295,6001
     - 코스피, 코스닥, 나스닥, 환율 
     - "," 기준으로 구분 됩니다.
     - 낱개로도 요청 가능합니다.

# websocket 동작 확인은 오후 5시 30분 이전까지 유효합니다.

# 9시 이전에는 어제자 종가가 오늘 가격이랑 동일하게 표기되는 문제 
#     - 장 시작 전이라 오늘 지수가 아직 반영 안됨

####################
## 국내 지수 코드  ##
####################
0001 종합(코스피)
1001 KOSDAQ
6295 NASDAQ-100 Total Return Index
6001 미국달러선물