# 네이버 스마트플레이스 데이터 수집기

네이버 스마트플레이스의 각 영역별 통계 데이터를 자동으로 수집하는 도구입니다.

## 구조

```
Nov.25__naverplace.scrapper/
├── main.py                    # 메인 실행 파일
├── modules/                   # 모든 모듈
│   ├── __init__.py
│   ├── naverplace_login.py    # 로그인 모듈
│   ├── base_scraper.py        # 베이스 스크래퍼 클래스
│   └── place_hourly_inflow_graph.py  # 플레이스 시간별 유입 그래프 모듈
└── data/naverplace/          # 수집된 데이터 저장 폴더
    └── place_hourly_inflow_graph/  # 플레이스 시간별 유입 그래프 데이터
```

## 사용 방법

### 기본 실행

```bash
python main.py
```

### 실행 흐름

1. **로그인**: 네이버 스마트플레이스에 자동 로그인
2. **데이터 수집**: 각 모듈을 순차적으로 실행하여 데이터 수집
   - 각 모듈은 독립적으로 실행되며, 각각의 폴더에 데이터 저장
   - 각 모듈은 `start_date`와 `end_date` 파라미터를 받아 날짜 범위 설정
3. **세션 종료**: 브라우저 세션 종료

### 날짜 파라미터

각 모듈은 `start_date`와 `end_date` 파라미터를 받습니다:
- 형식: `"YYYY-MM-DD"` (예: `"2025-11-15"`)
- 기본값: `start_date="2025-11-15"`, `end_date="2025-11-15"`

### 파일명 형식

- **CSV 파일**: `{모듈명}__{시작일}_{종료일}.csv`
  - 예: `place_hourly_inflow_graph__20251115_20251115.csv`
- **JSON 파일**: `{모듈명}_{타임스탬프}.json`

## 모듈 추가 방법

새로운 데이터 수집 모듈을 추가하려면:

1. `modules/` 폴더에 새 모듈 파일 생성 (예: `smartcall_statistics.py`)
2. `BaseScraper`를 상속받아 클래스 구현:

```python
from .base_scraper import BaseScraper
from playwright.async_api import Page

class SmartcallStatisticsScraper(BaseScraper):
    def __init__(self, username: str, password: str, start_date: str = None, end_date: str = None, output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL이나 기타 설정 초기화
    
    def get_module_name(self) -> str:
        return "smartcall_statistics"
    
    async def scrape(self, page: Page) -> dict:
        # 데이터 수집 로직 구현
        # self.start_date, self.end_date 사용 가능
        return {"data": "..."}
```

3. `modules/__init__.py`에 모듈 추가
4. `main.py`에서 스크래퍼 등록:

```python
from modules import SmartcallStatisticsScraper

collector.register_scraper(
    SmartcallStatisticsScraper(
        username, 
        password,
        start_date="2025-11-15",
        end_date="2025-11-15"
    )
)
```

## 데이터 저장 위치

- 기본 경로: `data/naverplace/{module_name}/`
- 각 모듈별로 폴더가 자동 생성됨
- JSON과 CSV 형식으로 저장

## 요구사항

- Python 3.8+
- playwright
- pandas

## 설정

자격증명은 `../data/info_naver.csv` 파일에 저장되어야 합니다.
CSV 형식: 첫 번째 행에 username, password

