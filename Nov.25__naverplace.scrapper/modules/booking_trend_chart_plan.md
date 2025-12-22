# Booking Trend Chart 데이터 수집 계획

## 현재 상황 분석

### 발견된 문제점
1. **React Fiber 탐색 실패**: Canvas와 Container의 React Props에서 차트 데이터를 찾지 못함
   - Container React Props keys: `['className', 'children']`만 존재
   - Canvas React Props keys: 출력되지 않음 (빈 배열 또는 접근 불가)

2. **차트 라이브러리 미감지**: Chart.js, ECharts 등이 감지되지 않음
   - Chart.js instances: 0
   - React는 감지되지만 차트 데이터 구조를 찾지 못함

3. **네트워크 요청은 캡처되지만 활용 안 됨**
   - API 응답은 캡처하고 있음 (`bucket=day_trend`, `bucket=bookingCo` 등)
   - 하지만 실제 데이터 파싱 및 활용은 하지 않음

### 네트워크 요청 분석
로그에서 확인된 API 엔드포인트:
- `https://partner.booking.naver.com/api/businesses/603738/reports?bucket=day_trend...`
- `https://partner.booking.naver.com/api/businesses/603738/reports?bucket=bookingCo...`
- `https://partner.booking.naver.com/api/businesses/603738/reports?bucket=cancelled...`
- `https://partner.booking.naver.com/api/businesses/603738/reports?bucket=price_sum...`

## 데이터 수집 전략

### 전략 1: 네트워크 API 응답 활용 (우선순위 1) ⭐
**장점:**
- 가장 신뢰할 수 있는 데이터 소스
- 체크박스 변경 시 새로운 API 요청이 발생할 가능성 높음
- 구조화된 JSON 데이터로 파싱 용이

**구현 방법:**
1. 체크박스 변경 후 발생하는 네트워크 요청 모니터링
2. `bucket` 파라미터와 체크박스 피쳐 매핑
3. API 응답에서 날짜별 데이터 추출

**예상 API 응답 구조:**
```json
{
  "dates": ["2025-12-01", "2025-12-02", ...],
  "data": [10, 15, 20, ...],
  "feature": "신청"
}
```

### 전략 2: React Fiber 깊이 탐색 강화 (우선순위 2)
**현재 문제:**
- React Fiber 탐색 깊이가 부족할 수 있음 (200단계)
- stateNode 확인은 추가했지만 더 많은 속성 확인 필요

**개선 방안:**
1. React Fiber 탐색 깊이 증가 (200 → 500단계)
2. 모든 가능한 속성 탐색 (alternate, dependencies 등)
3. 차트 컴포넌트의 실제 위치 찾기

### 전략 3: Canvas 직접 분석 (우선순위 3)
**방법:**
- Canvas의 이미지 데이터를 읽어서 차트 데이터 역추출
- 복잡하고 정확도가 낮을 수 있음

### 전략 4: Hover 방식 최적화 (Fallback)
**현재 상태:**
- 작동하지만 매우 느림 (30개 포인트 × 5개 y 위치 × 1초 = 최소 150초)

**최적화 방안:**
1. 데이터 포인트 수를 정확히 파악하여 불필요한 hover 제거
2. y 위치 탐색 범위 축소
3. 병렬 처리 (불가능 - 순차적 hover 필요)

## 권장 구현 순서

### Phase 1: 네트워크 API 분석 및 추출 (즉시 구현)
1. 체크박스 변경 시 발생하는 네트워크 요청 패턴 분석
2. API 응답 구조 파악
3. 데이터 추출 메서드 구현

### Phase 2: React Fiber 탐색 강화
1. 탐색 깊이 증가
2. 더 많은 속성 확인
3. 디버깅 정보 강화

### Phase 3: 통합 및 최적화
1. 네트워크 API 우선 사용
2. 실패 시 React Fiber 탐색
3. 최종 Fallback: Hover 방식

## 예상 API 엔드포인트 패턴

체크박스 피쳐별 API 요청 패턴:
- 신청: `bucket=day_trend` 또는 `bucket=bookingCo`
- 확정: `bucket=confirmed`
- 취소: `bucket=cancelled`
- 완료: `bucket=completed`

## 구현 체크리스트

- [x] 네트워크 요청 필터링 개선 (reports API만 캡처)
- [x] API 응답 파싱 메서드 구현 (`extract_chart_data_from_api`)
- [x] 체크박스 피쳐와 API bucket 매핑 (feature_bucket_map)
- [x] 데이터 추출 우선순위 설정 (API > JS > Hover)
- [x] 디버깅 정보 강화 (API 응답 구조 분석)
- [x] 에러 핸들링 및 Fallback 로직
- [ ] 실제 API 응답 구조 확인 및 파싱 로직 개선 (실행 후 필요시)

## 구현 완료 사항

### 1. API 데이터 추출 메서드 구현
- `extract_chart_data_from_api()` 메서드 추가
- 다양한 API 응답 구조 지원:
  - `{dates: [...], data: [...]}`
  - `{labels: [...], datasets: [{data: [...]}]}`
  - `[{date: ..., value: ...}, ...]`
  - `[value1, value2, ...]`

### 2. 데이터 추출 우선순위 변경
**이전:** JS > Hover  
**현재:** API > JS > Hover

### 3. 체크박스 피쳐 매핑
```python
feature_bucket_map = {
    '신청': ['day_trend', 'bookingCo'],
    '확정': ['confirmed'],
    '취소': ['cancelled'],
    ...
}
```

### 4. 결과 데이터 구조 개선
- `api_data`: API에서 추출한 원본 데이터
- `data_source`: 데이터 출처 표시 ("api", "js", "hover")

## 다음 단계

1. **실제 실행 및 테스트**
   - API 응답 구조 확인
   - 파싱 로직 필요시 조정

2. **성능 모니터링**
   - API 추출 성공률 확인
   - Fallback 빈도 확인

3. **추가 최적화**
   - API 응답 구조가 확인되면 파싱 로직 정확도 향상
   - React Fiber 탐색 개선 (필요시)
