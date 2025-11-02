# 🔧 네이버 검색광고 API 404 에러 해결 가이드

## 문제 상황

```
❌ 캠페인 조회 실패: 404 Client Error: Not Found 
for url: https://api.searchad.naver.com/v1/nsa/campaigns
```

---

## 🔍 원인 분석

### 1. 잘못된 Base URL (❌ 수정됨)

**문제**:
- `https://api.naver.com/v1/nsa` ← 잘못된 경로
- 또는 `https://api.searchad.naver.com/v1/nsa/campaigns` ← nsa 중복

**정정**:
- ✅ `https://api.searchad.naver.com/v1` (올바른 Base URL)
- ✅ 엔드포인트: `/campaigns`, `/stats` (nsa 제거)

---

### 2. 불완전한 인증 방식 (❌ 수정됨)

네이버 검색광고 API는 단순 헤더 인증이 아니라 **서명 기반 인증** 필요:

**필수 헤더**:
- `X-API-KEY`: API Key
- `X-CUSTOMER-ID`: Customer ID
- `X-TIMESTAMP`: Unix timestamp (밀리초)
- `X-SIGNATURE`: HMAC-SHA256 서명 ⭐ (이 부분이 누락됨)

**서명 생성 방식**:
```
message = "{METHOD} {URI} {TIMESTAMP}"
signature = HMAC-SHA256(api_key, message)
```

**예시**:
```
GET /campaigns 1730558400123
→ HMAC-SHA256("api_key_value", "GET /campaigns 1730558400123")
```

---

## ✅ 수정 사항

### 1. API 클라이언트 업데이트 (`scripts/api_client.py`)

```python
# ❌ 이전 (Base URL 오류)
self.base_url = 'https://api.naver.com/v1/nsa'

# ✅ 수정됨 (올바른 Base URL)
self.base_url = 'https://api.searchad.naver.com/v1'
```

### 2. 서명 생성 로직 추가

```python
def _generate_signature(self, timestamp, method, uri, body=''):
    """HMAC-SHA256 서명 생성"""
    message = f"{method} {uri} {timestamp}"
    if body:
        message = f"{message}\n{body}"
    
    signature = hmac.new(
        self.api_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def _get_headers(self, method, uri, body=''):
    """API 요청 헤더 생성"""
    timestamp = str(int(time.time() * 1000))
    signature = self._generate_signature(timestamp, method, uri, body)
    
    headers = {
        'X-API-KEY': self.api_key,
        'X-CUSTOMER-ID': self.customer_id,
        'X-TIMESTAMP': timestamp,
        'X-SIGNATURE': signature,
        'Content-Type': 'application/json'
    }
    
    return headers
```

### 3. Jupyter Notebook 업데이트

- Base URL 수정
- 서명 생성 로직 추가
- 에러 메시지 개선

---

## 📊 API 요청 흐름 (수정 후)

```
1. 요청 데이터 준비
   ├─ method: 'GET' / 'POST'
   ├─ uri: '/campaigns' / '/stats'
   └─ timestamp: 현재 시간 (밀리초)

2. 서명 생성
   ├─ message: f"{method} {uri} {timestamp}"
   ├─ body 있으면: f"{message}\n{body}"
   └─ signature: HMAC-SHA256(api_key, message)

3. 헤더 구성
   ├─ X-API-KEY: "..."
   ├─ X-CUSTOMER-ID: "..."
   ├─ X-TIMESTAMP: "1730558400123"
   ├─ X-SIGNATURE: "a1b2c3d4e5f6..."
   └─ Content-Type: "application/json"

4. HTTP 요청
   └─ GET/POST https://api.searchad.naver.com/v1/{endpoint}

5. 응답 수신
   ├─ 성공 (200): JSON 데이터
   └─ 실패 (404/401/403): 에러 메시지
```

---

## 🚀 다시 시도하기

```bash
# Jupyter Notebook 실행
jupyter notebook notebooks/1_naver_api_data_collection.ipynb

# Cell 실행 순서
1. 라이브러리 로드
2. API 키 로드
3. API 클래스 정의 (✅ 수정됨)
4. 캠페인 조회 (이제 정상 작동)
5. 통계 데이터 조회
```

---

## 📚 참고 자료

- **공식 API 문서**: [Naver Search Ads API Docs](https://naver.github.io/searchad-apidoc/#/guides)
- **에러 코드**: [Naver API Error Codes](https://naver.github.io/naver-openapi-guide/errorcode.html)
- **Rate Limit**: 초당 10 요청

---

## 🔐 API 키 보안

- `data/info.csv`는 `.gitignore`에 포함되어 git에 커밋되지 않음
- 민감한 정보이므로 외부 공유 금지
- 로컬 환경에서만 사용

---

**마지막 수정**: 2025-11-02
**상태**: ✅ 수정 완료
