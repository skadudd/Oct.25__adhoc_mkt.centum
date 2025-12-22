# 데이터 수집 실패 원인 분석

## 문제 상황

### 로그 분석
```
[Feature 1/9] Processing: 신청
  ⚠ No new API responses after checkbox check (using all responses)
  ✓ Found API response: ...bucket=bookingCo...
    Found 'result' array with 15 items
    First item sample: {'count': 10, 'metric': 'CANCELLED', 'day_trend': '2025-12-01', ...}
  ⚠ All 15 items were filtered out (filtered: 15)
    Feature '신청' expects metric: REQUESTED
    Actual metric values found: ['CANCELLED']
```

## 근본 원인

### 1. 체크박스 변경이 API 요청을 트리거하지 않음
- **증거**: "No new API responses after checkbox check"
- **의미**: 체크박스 변경 시 새로운 네트워크 요청이 발생하지 않음
- **결과**: 이미 로드된 API 응답만 사용 가능

### 2. 잘못된 bucket 선택
- **현재 로직**: `feature_bucket_map`에서 `['day_trend', 'bookingCo']` 순서로 선택
- **실제 상황**: `bookingCo` bucket에는 `CANCELLED` metric만 존재
- **문제**: `day_trend` bucket에 `REQUESTED` metric이 있을 가능성이 높지만, `bookingCo`가 먼저 선택됨

### 3. Bucket별 metric 분포 불일치
- `bookingCo` bucket: `CANCELLED` metric만 포함
- `day_trend` bucket: 다양한 metric 포함 (예상: `REQUESTED`, `ENDED` 등)
- **결론**: Bucket 선택 로직이 metric 분포를 고려하지 않음

## 해결 방안

### 방안 1: 모든 bucket을 확인하고 metric으로 필터링 (권장)
**장점:**
- 가장 확실한 방법
- Bucket과 metric의 관계를 정확히 파악 가능

**구현:**
1. 모든 reports API 응답을 확인
2. 각 응답에서 올바른 metric을 가진 데이터 추출
3. 가장 많은 데이터를 가진 응답 선택

### 방안 2: Bucket 우선순위 조정
**현재**: `['day_trend', 'bookingCo']`
**변경**: `['day_trend']`만 사용 (bookingCo 제외)

**단점:**
- `day_trend`에 모든 metric이 있는지 보장할 수 없음

### 방안 3: 체크박스 변경 후 실제 API 요청 확인
**가능성:**
- 체크박스 변경이 실제로 API 요청을 트리거하지만, 요청이 완료되기 전에 데이터를 추출하려고 시도
- 대기 시간 증가 필요

## 권장 해결책

**방안 1 구현**: 모든 bucket을 확인하고 metric으로 필터링하는 방식으로 변경

### 구현 단계
1. Bucket 선택 로직 제거
2. 모든 reports API 응답 확인
3. 각 응답에서 올바른 metric을 가진 데이터 추출
4. 가장 많은 데이터를 가진 응답 선택
