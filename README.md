# Auto Stock Trading Backend

이 프로젝트는 한국투자증권(KIS) 시세 API를 감싸는 Django REST 백엔드입니다.  
핵심 기능은 다음 세 가지입니다.

1. **인증** – KIS 액세스 토큰 발급 및 캐시 상태 조회 (`kis_auth` 앱)
2. **일별 시세** – 일별 종가 데이터를 정규화된 REST 형태로 제공 (`kis_prices` 앱)
3. **실시간 시세** – ETF/지수 기준 실시간 스냅샷(WebSocket) 제공 (`kis_realtime` + `indices` 앱)

아래 순서를 따라 로컬 환경에서 전체 기능을 실행하고 API를 호출해 보세요.

---

## 1. 저장소 클론 & 의존성 설치

```bash
git clone <REPO_URL>
cd auto_stock_trading_system_backend/auto_stock
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS
pip install --upgrade pip
pip install -r requirements.txt
```

> Python 3.11 이상을 권장합니다(현재 3.13에서 검증됨).

## 2. 환경 변수 설정

`.env.example`를 `.env`로 복사하거나 직접 `.env`를 만들어 아래 값을 입력하세요.

```
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443
KIS_APP_KEY=본인_APP_KEY
KIS_APP_SECRET=본인_APP_SECRET
KIS_APP_KEY_REAL=실계좌_APP_KEY        # 선택, 기본값은 KIS_APP_KEY
KIS_APP_SECRET_REAL=실계좌_APP_SECRET  # 선택, 기본값은 KIS_APP_SECRET
KIS_WS_BASE_URL=ws://ops.koreainvestment.com:31000
```

> `auto_stock/settings.py`에서 `.env`를 자동으로 로드합니다.

## 3. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

- `kis_realtime/0002_seed_default_symbols.py` 마이그레이션이 기본 ETF 심볼
  (`exchangeRate`, `kospi`, `kosdaq`, `nasdaq`)을 미리 추가해 실시간 API를 바로 사용할 수 있게 해줍니다.

Django 관리자 계정이 필요하면:

```bash
python manage.py createsuperuser
```

## 4. 개발 서버 실행

```bash
python manage.py runserver 0.0.0.0:8000
```

서버는 `http://localhost:8000/`에서 접속할 수 있습니다.

## 5. API 호출 순서

주요 엔드포인트와 `curl` 예시는 아래와 같습니다.

### 5.1 토큰 상태 확인

캐시된 KIS 액세스 토큰 정보를 확인합니다.

```bash
curl -X GET http://localhost:8000/api/kis/auth/token/
```

응답 예시:

```json
{
  "access_token": "eyJ...",
  "expires_at": 1731384000.0,
  "is_expired": false
}
```

### 5.2 일별 시세 REST API

KRX 심볼의 정규화된 일별 데이터를 조회합니다.

```bash
curl -G http://localhost:8000/api/kis/prices/daily/ \
     --data-urlencode "symbol=005930" \
     --data-urlencode "period=D"
```

`symbol`은 필수이며 `period`는 기본 `"D"`로 KIS 기간 코드와 동일합니다.

### 5.3 실시간 시세 API

저장된 심볼 또는 임의 코드에 대해 WebSocket 기반 스냅샷을 요청합니다.

1. **기본 심볼 전체 사용** (쿼리 파라미터 불필요):

```bash
curl http://localhost:8000/api/kis/realtime/quotes/
```

2. **특정 식별자만 지정**:

```bash
curl -G http://localhost:8000/api/kis/realtime/quotes/ \
     --data-urlencode "symbols=kospi,nasdaq"
```

3. **즉석 코드 조회** (DB에 자동 저장):

```bash
curl -G http://localhost:8000/api/kis/realtime/quotes/ \
     --data-urlencode "codes=005930,000660"
```

저장된 심볼을 확인/수정하려면:

```bash
# 목록 조회
curl http://localhost:8000/api/kis/realtime/symbols/

# 등록 또는 갱신
curl -X POST http://localhost:8000/api/kis/realtime/symbols/ \
     -H "Content-Type: application/json" \
     -d '{"identifier":"samsung","code":"005930","name":"Samsung Electronics"}'
```

### 5.4 지수(Indices) API

KIS 서비스를 조합해 만든 ETF 기반 지수 API입니다.

- 일별 지수: `GET /api/market/indices/`
- 실시간 지수: `GET /api/market/indices/realtime/`

`INDICES_CACHE_TTL_SECONDS`(기본 5초) 동안 캐시되어 반복 호출 시 부하가 낮습니다.

## 6. Swagger & Browsable API

서버 실행 후 `http://localhost:8000/swagger`로 이동하면 모든 엔드포인트를 확인하고 테스트할 수 있습니다.

---

### 팁 & 문제 해결

- `System check ... swagger ...` 경고는 path 설정과 관련된 기존 경고로 무시해도 됩니다.
- 실시간 시세는 `websocket-client` 패키지를 사용합니다(이미 requirements에 포함). 방화벽이 WebSocket 목적지에 대한 outbound를 허용하는지 확인하세요.
- 처음 `codes=` 쿼리로 호출하면 해당 코드가 DB에 자동 등록됩니다. `/api/kis/realtime/symbols/`나 Django 관리자에서 삭제/수정할 수 있습니다.

이제 로컬 환경에서 KIS 토큰 관리, 일별 시세, 실시간 ETF 시세까지 모두 실험할 수 있습니다. 즐거운 개발 되세요!
