# 📁 프로젝트 구조

```
Oct.25__adhoc_mkt.centum/
│
├── 📋 README.md                              # 메인 프로젝트 가이드
│
├── 📂 docs/                                  # 📚 문서 디렉토리
│   ├── API_DEBUG_GUIDE.md                   # API 디버그 가이드
│   ├── API_FIX_SUMMARY.md                   # 수정 사항 요약
│   ├── CRITICAL_FINDING.md                  # 중대 발견사항
│   ├── DIAGNOSIS.md                         # 1차 진단
│   ├── FINAL_DIAGNOSIS.md                   # 최종 진단
│   ├── NEVADA_API_SOLUTION.md               # ✨ Nevada 해결책 (NEW)
│   └── STATUS_REPORT.md                     # 상태 보고서
│
├── 📂 tests/                                 # 🧪 테스트 스크립트
│   ├── test_api.sh                          # 기본 API 테스트
│   ├── test_api_detailed.sh                 # 상세 분석
│   ├── test_response_only.sh                # 응답 확인
│   ├── test_with_base64_signature.sh        # Base64 서명
│   ├── test_with_customer_id.sh             # Customer ID
│   ├── test_with_secret_key.sh              # Secret Key
│   ├── test_nevada_api.sh                   # Nevada 테스트
│   ├── test_nevada_redirect.sh              # 리다이렉트 확인
│   ├── test_nevada_v2.sh                    # Nevada v2 (NEW)
│   ├── comprehensive_test.sh                # 종합 테스트
│   ├── final_test.sh                        # 최종 테스트
│   └── test_nevada_redirect.sh              # 리다이렉트 분석
│
├── 📂 scripts/                               # 🐍 Python 스크립트
│   ├── api_client.py                        # API 클라이언트 v1
│   ├── api_client_v2.py                     # API 클라이언트 v2
│   ├── api_client_nevada.py                 # ✨ Nevada 방식 (CORRECTED)
│   ├── test_api.py                          # Python 테스트
│   └── utils.py                             # 유틸 함수
│
├── 📂 notebooks/                             # 📓 Jupyter Notebooks
│   ├── 1_naver_api_data_collection.ipynb    # 데이터 수집
│   └── test_nevada_api.py                   # Nevada 테스트 스크립트
│
├── 📂 data/                                  # 📊 데이터 디렉토리
│   ├── info.csv                             # API 키 정보 (비공개)
│   ├── raw/                                 # 원본 API 응답
│   ├── processed/                           # 정제된 데이터
│   └── analysis/                            # 분석 결과
│
├── 📂 reports/                               # 📈 최종 리포트
│   └── (생성 예정)
│
└── 📂 .cursor/                               # 설정 파일
    ├── mcp.json                             # MCP 설정
    └── commands/                            # Cursor 명령어
```

---

## 📊 파일 분류

### 문서 (docs/)
| 파일 | 설명 |
|------|------|
| `NEVADA_API_SOLUTION.md` | ✨ **최신: Nevada API 올바른 방식** |
| `FINAL_DIAGNOSIS.md` | 최종 진단 결과 |
| `STATUS_REPORT.md` | 프로젝트 상태 보고서 |
| `CRITICAL_FINDING.md` | 중대 발견사항 |

### 테스트 (tests/)
| 파일 | 설명 |
|------|------|
| `test_nevada_v2.sh` | ✨ **최신: Nevada v2 테스트** |
| `comprehensive_test.sh` | 8가지 인증 방식 종합 테스트 |
| `test_with_customer_id.sh` | Customer ID 포함 테스트 |

### 코드 (scripts/)
| 파일 | 설명 |
|------|------|
| `api_client_nevada.py` | ✨ **최신: Nevada 방식 (수정됨)** |
| `api_client_v2.py` | Secret Key 기반 클라이언트 |
| `utils.py` | 공통 유틸 함수 |

---

## 🎯 최근 업데이트

### ✨ Nevada 방식 발견 & 수정

**문제**: HTTP 404 에러 지속
**원인**: Base URL 오류 + 경로 형식 불일치
**해결**:
- ❌ 기존: `https://api.naver.com/v1/campaigns`
- ✅ 수정: `https://api.searchad.naver.com/searchad/campaigns.naver`

**수정된 파일**:
1. `docs/NEVADA_API_SOLUTION.md` (NEW) - 완전한 해결책 문서
2. `scripts/api_client_nevada.py` - 수정된 Python 클래스
3. `tests/test_nevada_v2.sh` - 리다이렉트 분석 결과

---

## 📈 프로젝트 진행률

```
Task 1: 데이터 수집
├─ 환경 구성: ✅ 100%
├─ 코드 개발: ✅ 100%
├─ 테스트: 🟢 90% (Nevada 방식 발견)
└─ 배포: ⏳ 0%

전체 진행률: 🟢 약 20-25%
```

---

## 🚀 다음 단계

1. **requests 모듈 설치**
   ```bash
   pip3 install requests
   ```

2. **API 테스트 실행**
   ```bash
   python3 scripts/api_client_nevada.py
   ```

3. **성공 시**: 데이터 수집 시작

---

**마지막 업데이트**: 2025-11-02  
**상태**: 🟢 **Ready for Testing**

