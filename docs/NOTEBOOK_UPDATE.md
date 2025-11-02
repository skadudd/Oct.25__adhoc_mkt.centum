# 📓 Notebook 업데이트 완료

**작성일**: 2025-11-02  
**상태**: ✅ **완료**

---

## 📝 업데이트 내용

### 1️⃣ Cell 0: API 정보 업데이트
```markdown
- Base URL: https://api.searchad.naver.com ✨
- 경로 형식: /searchad/{resource}.naver ✨
- 인증: X-API-KEY, X-Customer, X-TIMESTAMP, X-SIGNATURE
```

### 2️⃣ Cell 2: Secret Key 추가
```python
naver_api_key = "..."
naver_customer_id = {CUSTOMER_ID}
```

### 3️⃣ Cell 4: 인증 방식 설명 업데이트
```
인증 방식 (python_nevada 기반):
- X-API-KEY: 액세스라이선스
- X-Customer: 고객 ID (숫자)
- X-TIMESTAMP: Unix timestamp (밀리초)
- X-SIGNATURE: HMAC-SHA256(secret_key, "{METHOD} {PATH} {TIMESTAMP}")

경로 형식:
- /searchad/apiservice.naver (시간 조회)
- /searchad/campaigns.naver (캠페인)
- /searchad/campaigns/{id}/adgroups.naver (광고그룹)
- /searchad/campaigns/{id}/adgroups/{id}/keywords.naver (키워드)
```

### 4️⃣ Cell 5: API 클래스 전체 교체

**새 클래스**: `NaverSearchAdsConnector` (Nevada 방식)

```python
class NaverSearchAdsConnector:
    def __init__(self, api_key, secret_key, customer_id):
        self.api_key = api_key
        self.secret_key = secret_key
        self.customer_id = str(customer_id)
        self.base_url = 'https://api.searchad.naver.com'
    
    def _generate_signature(self, method, path, timestamp):
        message = f"{method} {path} {timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
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
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(
                    url, headers=headers,
                    data=body.encode('utf-8') if body else None,
                    timeout=10
                )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API 요청 실패: {e}")
            return None
    
    def get_datetime(self):
        return self._request('GET', '/searchad/apiservice.naver')
    
    def get_campaigns(self):
        return self._request('GET', '/searchad/campaigns.naver')
    
    def get_keywords(self, campaign_id, ad_group_id):
        path = f'/searchad/campaigns/{campaign_id}/adgroups/{ad_group_id}/keywords.naver'
        return self._request('GET', path)
    
    def get_statistics(self, start_date, end_date, time_unit='DAY'):
        path = '/searchad/stats.naver'
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'timeUnit': time_unit
        }
        body = json.dumps(payload, ensure_ascii=False)
        return self._request('POST', path, body)
```

---

## 🎯 주요 변경 사항

| 항목 | 기존 | 수정됨 |
|------|------|--------|
| Base URL | `https://api.searchad.naver.com/v1` | `https://api.searchad.naver.com` ✨ |
| 경로 형식 | `/campaigns`, `/stats` | `/searchad/campaigns.naver` ✨ |
| Customer ID 헤더 | `X-CUSTOMER-ID` | `X-Customer` ✨ |
| 서명 생성 키 | API Key | Secret Key ✨ |
| 클래스명 | `NaverSearchAdsAPI` | `NaverSearchAdsConnector` ✨ |

---

## 🚀 다음 단계

1. **Jupyter Notebook 실행**
   ```bash
   jupyter notebook notebooks/1_naver_api_data_collection.ipynb
   ```

2. **Cell 순서대로 실행**
   - Cell 0: 라이브러리 로드 ✅
   - Cell 1: API 키 로드 ✅
   - Cell 2: API 클래스 정의 ✅
   - Cell 3: 캠페인 조회 (🟡 테스트)
   - Cell 4: 통계 조회 (🟡 테스트)
   - Cell 5: 데이터 정제 및 저장

3. **예상 결과**
   ```
   ✅ HTTP 200 응답 (더 이상 404 에러 없음)
   ✅ 캠페인 데이터 수집
   ✅ 통계 데이터 저장
   ```

---

## 📊 상태 체크리스트

- [x] API 문서 업데이트
- [x] Secret Key 추가
- [x] 인증 방식 설명 업데이트
- [x] API 클래스 교체
- [ ] Notebook 실행 및 테스트 (다음 단계)

---

## 📌 참고 사항

### Nevada 방식의 특징
1. **Base URL 고정**: `https://api.searchad.naver.com`
2. **경로에 .naver 확장자**: 모든 경로가 `.naver`로 끝남
3. **Customer ID**: 숫자 형식 (X-Customer 헤더)
4. **Secret Key 서명**: API Key가 아닌 Secret Key 사용
5. **Hex 서명**: Base64 인코딩 없이 hex format 사용

### 리다이렉트 자동 처리
- `https://api.naver.com` → `https://api.searchad.naver.com` (자동 리다이렉트)
- 직접 `https://api.searchad.naver.com` 사용 권장

---

**업데이트 완료**: 2025-11-02  
**Notebook 경로**: `notebooks/1_naver_api_data_collection.ipynb`  
**상태**: ✅ **Ready to Run**

