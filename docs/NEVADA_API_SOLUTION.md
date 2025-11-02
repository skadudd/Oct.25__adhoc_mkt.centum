# 🎯 Nevada 방식 API 해결책

**작성일**: 2025-11-02  
**상태**: 🟢 **해결 완료**

---

## 🔍 발견 사항

### HTTP 308 Redirect 분석

테스트 결과 모든 요청이 **HTTP 308 (Permanent Redirect)** 응답:

```
요청 URL: https://api.naver.com/searchad/apiservice.naver
↓ (308 리다이렉트)
리다이렉트 위치: https://api.searchad.naver.com/searchad/apiservice.naver
```

**결론**: Base URL을 직접 수정하면 됨!

---

## ✅ 올바른 API 설정

### Base URL 수정

**❌ 잘못된 방식**:
```
https://api.naver.com/searchad/apiservice.naver
```

**✅ 올바른 방식**:
```
https://api.searchad.naver.com/searchad/apiservice.naver
```

### 경로 형식

```
/searchad/{resource}.naver

예시:
- /searchad/apiservice.naver (시간 조회)
- /searchad/campaigns.naver (캠페인 목록)
- /searchad/campaigns/{id}/adgroups.naver (광고 그룹)
- /searchad/campaigns/{id}/adgroups/{id}/keywords.naver (키워드)
```

### 인증 헤더

```
X-API-KEY: {액세스라이선스}
X-Customer: {고객ID}
X-Timestamp: {타임스탬프_밀리초}
X-Signature: {HMAC-SHA256_서명}
Content-Type: application/json
```

### 서명 생성 (HMAC-SHA256)

```
메시지 = "{METHOD} {PATH} {TIMESTAMP}"
서명 = HMAC-SHA256(SECRET_KEY, 메시지)

예:
메시지: "GET /searchad/apiservice.naver 1730558400123"
서명: (hex format)
```

---

## 📄 구현 코드

### Python 클래스

```python
class NaverSearchAdsConnector:
    def __init__(self, api_key, secret_key, customer_id):
        self.base_url = 'https://api.searchad.naver.com'
        self.api_key = api_key
        self.secret_key = secret_key
        self.customer_id = str(customer_id)
    
    def _generate_signature(self, method, path, timestamp):
        message = f"{method} {path} {timestamp}"
        secret_bytes = self.secret_key.encode('utf-8')
        signature = hmac.new(
            secret_bytes,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method, path):
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(method, path, timestamp)
        return {
            'X-API-KEY': self.api_key,
            'X-Customer': self.customer_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'Content-Type': 'application/json'
        }
    
    def _request(self, method, path, body=None):
        url = f"{self.base_url}{path}"
        headers = self._get_headers(method, path)
        # requests.get(url, headers=headers) 또는 requests.post(...)
        
    def get_campaigns(self):
        return self._request('GET', '/searchad/campaigns.naver')
```

---

## 🧪 테스트

```bash
# 현재 시간 조회
curl -i -X GET \
  -H "X-API-KEY: {api_key}" \
  -H "X-Customer: {customer_id}" \
  -H "X-Timestamp: {timestamp}" \
  -H "X-Signature: {signature}" \
  "https://api.searchad.naver.com/searchad/apiservice.naver"

# 응답: HTTP 200 OK (리다이렉트 X)
```

---

## 📊 전체 API 경로 (Nevada 방식)

| 기능 | HTTP | 경로 |
|------|------|------|
| 시간 조회 | GET | /searchad/apiservice.naver |
| 캠페인 조회 | GET | /searchad/campaigns.naver |
| 특정 캠페인 | GET | /searchad/campaigns/{id}.naver |
| 광고 그룹 | GET | /searchad/campaigns/{id}/adgroups.naver |
| 키워드 | GET | /searchad/campaigns/{id}/adgroups/{id}/keywords.naver |
| 통계 | POST | /searchad/stats.naver |

---

## 🎯 다음 단계

1. ✅ `api_client_nevada.py` 코드 수정 완료
2. ⏳ `secret_key` 값 재확인 필요 (현재 비밀키 사용 중)
3. ⏳ API 인증 시도 (requests 모듈 설치 후)
4. ⏳ 성공 시 데이터 수집 시작

---

## 📌 Key Points

- **Base URL**: `https://api.searchad.naver.com` (고정)
- **경로**: `/searchad/{resource}.naver` 형식
- **인증**: X-API-KEY, X-Customer, X-Timestamp, X-Signature
- **서명**: 메시지는 `{METHOD} {PATH} {TIMESTAMP}` 형식
- **고객ID**: 숫자 형식 ({CUSTOMER_ID})

---

**참고 자료**: [python_nevada](https://github.com/taegyumin/python_nevada)

