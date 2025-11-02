## 센텀 의료기관 네이버 검색광고 ROI 분석 프로젝트

### 📊 프로젝트 개요

의료기관 의사가 네이버 검색광고의 효율성에 대해 의문을 가지고 있는 상황에서, 마케팅 분석가로서 현재 데이터를 활용하여 **광고 효과를 검증**하고 **의사결정을 지원**하는 프로젝트입니다.

**분석 기간**: 2025-10-27 ~ 2025-11-30

---

### 🎯 분석 목표

1. **광고 효율성 검증**: 네이버 검색광고의 ROI, ROAS, CPA 분석
2. **다중 경로 추적**: 검색광고 클릭 → 예약(온/오프라인) 전환 경로 분석
3. **다매체 기여도 평가**: 검색광고 vs 자연검색 vs 디스플레이 등 기여도 정량화
4. **의사결정 지원**: 광고 매체 지속/종료 판단 근거 제공

---

### 📋 현황 분석

**문제점**:
- 클릭 수는 많으나 직접 전환이 적음
- 제한된 쿠키 추적으로 인한 분석 어려움
- 다중 전환 경로(온라인 예약 + 전화 예약)로 인한 복잡성
- 다중 매체 운영(네이버, 유튜브, 플레이스, 토스 등)

**데이터 소스**:
- 매체: 네이버 검색광고, 플레이스, 토스, 유튜브
- 전환: 전화 예약, 온라인 예약
- 추적: 스마트로그 (GA 유사 SaaS)

---

### 📁 프로젝트 구조

```
Oct.25__adhoc_mkt.centum/
├── readme.md                              # 프로젝트 가이드
├── data/
│   ├── info.csv                          # API 키 정보 (git ignored)
│   ├── raw/                              # 원본 데이터 (API 응답)
│   ├── processed/                        # 정제된 데이터
│   └── analysis/                         # 분석 결과
├── notebooks/
│   ├── 1_naver_api_data_collection.ipynb      # Task 1: 네이버 API 데이터 수집
│   ├── 2_smartlog_conversion_data.ipynb       # Task 2: 스마트로그 전환 데이터
│   ├── 3_data_integration.ipynb               # Task 3: 데이터 통합 및 기초통계
│   ├── 4_attribution_modeling.ipynb           # Task 4: 어트리뷰션 모델링
│   ├── 5_regression_analysis.ipynb            # Task 5: 회귀분석
│   ├── 6_mmm_analysis.ipynb                   # Task 6: MMM 분석
│   └── ...
├── scripts/
│   ├── utils.py                          # 공통 유틸 함수
│   ├── api_client.py                     # API 클라이언트
│   └── config.py                         # 설정 파일
└── reports/
    └── final_report.md                   # 최종 의사결정 리포트
```

---

### 📊 11단계 분석 프로세스

| # | 태스크 | 상태 | 산출물 |
|---|--------|------|--------|
| 1 | 네이버 검색광고 API 데이터 수집 | 🔄 진행중 | 일별 캠페인/키워드 성과 |
| 2 | 스마트로그 전환 데이터 수집 | ⏳ 대기중 | 사용자 여정 + 전환 경로 |
| 3 | 데이터 통합 및 기초 통계 | ⏳ 대기중 | CTR, CVR, CPC, ROAS, CPA |
| 4 | 어트리뷰션 모델링 | ⏳ 대기중 | 4가지 모델 기여도 |
| 5 | 회귀 분석 | ⏳ 대기중 | 광고비-전환 인과성 |
| 6 | MMM 다매체 기여도 | ⏳ 대기중 | 다매체 기여도 + 예산최적화 |
| 7 | 키워드 ROI 분석 | ⏳ 대기중 | 키워드 세분화(High/Mid/Low) |
| 8 | 경쟁사 벤치마킹 | ⏳ 대기중 | CPC 비교 + 입찰전략 |
| 9 | 증분성 테스트 | ⏳ 대기중 | 순증분 ROI 검증 |
| 10 | 최종 의사결정 리포트 | ⏳ 대기중 | 권고사항 + 시뮬레이션 |
| 11 | 모니터링 대시보드 | ⏳ 대기중 | 자동 업데이트 대시보드 |

---

### 🚀 시작하기

#### 1. 환경 설정
```bash
# Python 3.9+ 필요
pip install pandas numpy requests matplotlib seaborn scikit-learn statsmodels

# 선택사항: Jupyter Notebook
pip install jupyter
```

#### 2. API 키 설정
`data/info.csv` 파일에 Naver Search Ads API 키 입력:
```csv
media,key,scr
nsa,YOUR_API_KEY,YOUR_CUSTOMER_ID
```

#### 3. Task 1 실행
```bash
jupyter notebook 1_naver_api_data_collection.ipynb
```

---

### 📚 API 참고 자료

- **Naver Search Ads API Docs**: [https://naver.github.io/searchad-apidoc/#/guides](https://naver.github.io/searchad-apidoc/#/guides)
- API 인증: X-API-KEY, X-CUSTOMER-ID 헤더 필수
- Rate Limit: 초당 10 요청 제한

---

### 📞 주요 지표 정의

| 지표 | 공식 | 해석 |
|------|------|------|
| **CTR** | 클릭수 / 노출수 | 광고 클릭 유도율 |
| **CVR** | 전환수 / 클릭수 | 방문객 예약 전환율 |
| **CPC** | 광고비 / 클릭수 | 클릭당 평균 비용 |
| **CPA** | 광고비 / 전환수 | 전환당 평균 비용 |
| **ROAS** | 전환 매출 / 광고비 | 광고비 대비 매출 비율 |
| **ROI** | (매출 - 비용) / 광고비 | 광고비 대비 순이익 비율 |

---

### 🔍 데이터 품질 기준

- ✅ API 데이터 성공 수집
- ✅ 결측치율 < 5%
- ✅ 시계열 데이터 정합성 확인
- ✅ 이상치 탐지 및 처리

---

### 📝 분석 방법론

1. **기초 분석**: 기술통계, 시각화
2. **어트리뷰션**: Last-click, First-click, Linear, Time-decay 4가지 모델
3. **인과성 분석**: 회귀분석(OLS), 시계열 분석(ARIMA)
4. **고급 분석**: MMM (Marketing Mix Modeling), Incrementality Testing
5. **최적화**: ROI 시뮬레이션, 예산 배분 최적화

---

### 📊 최종 결과물

1. **기술통계 대시보드**: 매체별/키워드별 성과 실시간 모니터링
2. **어트리뷰션 보고서**: 각 매체의 전환 기여도 정량화
3. **MMM 분석**: 다매체 증분 효과 측정
4. **의사결정 리포트**: 광고 지속/종료 판단 근거 + 최적화 전략
5. **예측 대시보드**: 광고비 변화 시나리오별 기대 효과

---

### 📌 주의사항

- API 키는 `data/info.csv`에 저장하며, git에 커밋되지 않도록 `.gitignore`에 포함
- 의료 데이터의 민감성을 고려하여 개인정보 제외 분석
- 모든 분석 결과는 통계적 유의성 검증 필수

---

### 👤 담당자

- **분석가**: 님영
- **프로젝트 기간**: 2025-10-27 ~ 2025-11-30
- **최종 리포트 제출**: 2025-11-30

---

**생성일**: 2025-10-27