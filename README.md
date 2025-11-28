# Auto Stock Trading Server repository

### 🔎 About CashCow 
CashCow는 주식 자동 매매 자동화를 위한 django 애플리케이션입니다. <br>
한국투자증권 API와 실시간 시세 데이터, RSI 지표를 통해 자동 매매 서비스를 제공합니다.<br>

사용자가 단기 투자 전략을 선택하면 시스템이 시장 데이터를 모니터링하여 자동으로 매수·매도 조건을 판단하고 주문을 실행합니다.

### 🏷️ 주요 기능 기술 
1. 자동 매매 
   * 지표 기반(RSI, 이동평균선 등) 자동 매매 로직
   * Celery 기반 비동기 작업  
   * 한국 투자 증권 서버로 주문 요청 
    
2. 한국 투자 증권 API 연동 
   * WebSocket 기반 시세 데이터 수신
   * REST 기반 일별 시세 데이터 수신 
   * REST 기반 시가 총액 상위 10개 종목 조회 
   * REST 기반 지수 조회 
   * KIS 접근 토큰 발급 및 캐싱
   * 사용자 계좌 조회 

---

### 1. 저장소 클론 & 의존성 설치

```bash
git clone https://github.com/Hybrid05-team03/auto_stock_trading_system_backend.git
cd auto_stock_trading_system_backend/auto_stock

# 가상 환경 생성 
python -m  venv <가상환경명> 

# 가상 환경 활성화 
source <가상환경명>/Scripts/activate # Windows
source <가상환경명>/bin/activate  # Linux/macOS

# 의존성 설치 
pip install --upgrade pip
pip install -r requirements.txt

# 데이터베이스 마이그레이션 
python manage.py makemigrations
python manage.py migrate
```

### 2. 서버 실행 사전 준비 
> Python 버전 : 3.11 이상 사용을 권장합니다. <br>
> Redis(6379)가 실행 중이어야 합니다.  <br>
> Mariadb(3306)가 실행 중이어야 합니다.  <br>

### 3. 서버 실행 
```bash
python manage.py runserver # 서버 실행 
python -m kis.websocket.util.kis_ws_client # 웹 소켓 연결 모듈 실행  
celery -A auto_stock worker -l info # 비동기 작업 워커 실행 
celery -A auto_stock beat -l info   # 비동기 작업 정기 실행 
```

### 4. 문서 (Documentation) 
* _**📌 API 명세서**_ 
https://hb05-infra.notion.site/API-2a402d82d9c380079068ef2ca8b6fc2e?source=copy_link<br><br>
* **_⚒️ 프로젝트 구조_**
    ```bash
    auto_stock/                       # 프로젝트 루트
    ├── .env                          # 환경 변수 파일
    ├── auto_stock/                   # Django 프로젝트 설정
    ├── common/                       # Swagger 및 공통 설정
    ├── kis/                          # KIS 통신 모듈
    │   ├── api/                      # REST API 요청
    │   ├── auth/                     # 토큰 발급
    │   ├── constants/                # 상수 정의
    │   ├── data/                     # 종목 코드 파일
    │   └── websocket/                # WebSocket 모듈
    ├── kis_test/                     # 테스트용 KIS 클라이언트
    └── trading/                      # 자동 매매 전략/처리
    ```

