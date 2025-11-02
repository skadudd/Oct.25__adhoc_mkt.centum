# 🔍 네이버 검색광고 API 404 에러 - 근본 원인 진단

## 현재 상태

```
HTTP/2 404
date: Sun, 02 Nov 2025 11:06:26 GMT
content-length: 0
```

요청이 서버에 도달하고 있지만, 인증 실패로 404가 반환되고 있습니다.

---

## 🚨 근본 원인 추정

### 1. **SCR 값의 역할**

**발견**:
- `scr` 컬럼의 값은 Base64로 인코딩됨
- 디코딩하면 바이너리 데이터 (UTF-8 불가)
- `scr` ≠ Customer ID 일 가능성 **높음**

**원래 API Key와 SCR 값**:
```
API Key: {API_KEY}

SCR 디코딩:
{API_KEY}
```

**결론**: SCR은 API Key와 다른 바이너리 값이며, 실제 **Customer ID는 아님**!

---

## 📋 문제 분석 체크리스트

| 항목 | 현재 | 필요 |
|------|------|------|
| Base URL | ✅ https://api.searchad.naver.com/v1 | 정확함 |
| X-API-KEY | ✅ 74자 16진수 | 정확함 |
| X-CUSTOMER-ID | ❌ Base64 인코딩된 값 | **실제 Customer ID 필요** |
| X-TIMESTAMP | ✅ 밀리초 단위 Unix | 정확함 |
| X-SIGNATURE | ✅ HMAC-SHA256 | 생성 방식 정확함 |

---

## 💡 해결 방안

### Option 1: 네이버 계정 정보에서 Customer ID 찾기

네이버 검색광고 관리자 페이지에서:
- 계정 설정 → API 정보
- 고객 ID 또는 Customer ID 확인
- 일반적으로 **숫자** 형식 (예: 123456789)

### Option 2: 공식 API 샘플 코드 확인

[https://github.com/naver/searchad-apidoc](https://github.com/naver/searchad-apidoc) 에서:
- 실제 요청 예제 확인
- 헤더 구성 방식 확인
- 인증 방식 재검증

### Option 3: API 테스트 도구 사용

네이버 검색광고 공식 문서의 "API 테스트" 기능:
- 웹 UI에서 직접 API 테스트
- 필요한 헤더 형식 확인
- 실제 응답 확인

---

## 🎯 다음 단계

1. **네이버 검색광고 관리자 페이지 접속**
   - 실제 Customer ID (숫자 형식) 확인
   - `data/info.csv`의 `scr` 컬럼을 실제 Customer ID로 업데이트

2. **API 요청 재시도**
   ```bash
   # 새로운 Customer ID로 테스트
   bash test_api_detailed.sh
   ```

3. **결과 확인**
   - HTTP 200: ✅ 성공 → 데이터 수집 시작
   - HTTP 401/403: 인증 재검증
   - HTTP 404: 다른 헤더 조합 시도

---

## 📌 요청 사항

**님영님께 확인 필요**:
1. 네이버 검색광고 관리자 페이지의 **실제 Customer ID** 값
2. 또는 API 키 발급 받은 네이버 고객지원 이메일/문서에서:
   - 정확한 Customer ID 형식
   - X-CUSTOMER-ID 헤더에 사용할 값

---

**생성**: 2025-11-02  
**상태**: 🔴 대기 - 실제 Customer ID 확인 필요
