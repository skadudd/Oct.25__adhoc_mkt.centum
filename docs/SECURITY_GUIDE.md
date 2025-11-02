# 🔒 보안 가이드

**작성일**: 2025-11-02  
**주제**: API 시크릿 정보 관리

---

## ⚠️ 중요 공지

**모든 API 시크릿 정보(API Key, Secret Key, Customer ID)는 코드/문서에 포함되지 않습니다.**

---

## 📋 API 정보 관리

### 1️⃣ 저장 위치 (유일)

```
data/info.csv  (Git에서 .gitignore로 제외됨)
```

**파일 구조**:
```csv
media,key,scr
nsa,{API_KEY},{CUSTOMER_ID}
```

### 2️⃣ 안전한 로드 방법

**Python에서**:
```python
import pandas as pd

api_info = pd.read_csv('data/info.csv')
api_key = api_info[api_info['media'] == 'nsa']['key'].values[0]
customer_id = api_info[api_info['media'] == 'nsa']['scr'].values[0]
```

**Bash에서**:
```bash
api_key=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
customer_id=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)
```

---

## 🚫 금지 사항

❌ **절대 하지 말 것**:
1. API Key를 코드에 하드코딩
2. Secret Key를 문서/주석에 기재
3. 시크릿 정보를 Git에 커밋
4. Jupyter Notebook에 시크릿 정보 작성
5. Slack/메일로 API 키 공유

---

## ✅ 권장 사항

✅ **해야 할 것**:
1. 모든 시크릿 정보는 `data/info.csv`에만 저장
2. 코드는 `data/info.csv`에서 동적으로 로드
3. 시크릿 정보 필요시 환경변수 사용
4. Git 커밋 전에 `git diff` 확인
5. `.gitignore`에 민감한 파일 등록

---

## 🔐 Secret Key 설정

**Secret Key는 환경 변수로 설정 권장**:

```bash
# 터미널에서
export NAVER_SECRET_KEY="your_secret_key_here"

# Python에서
import os
secret_key = os.getenv('NAVER_SECRET_KEY')
```

---

## 📝 체크리스트

코드 작성 후 반드시 확인:

- [ ] 코드에 API Key 하드코딩 없음
- [ ] 코드에 Secret Key 노출 없음
- [ ] 주석/docstring에 시크릿 정보 없음
- [ ] Markdown 문서에 시크릿 정보 없음
- [ ] `git diff`로 확인 후 커밋
- [ ] `data/info.csv`만 시크릿 저장

---

## 🔍 검증 방법

**코드에서 시크릿 정보 검색**:

```bash
# API Key 확인
grep -r "01000000" . --include="*.py" --include="*.ipynb" --include="*.md" --include="*.sh"

# Secret Key 확인
grep -r "AQAAAADSt" . --include="*.py" --include="*.ipynb" --include="*.md" --include="*.sh"

# 응답 없으면 ✅ 안전
```

---

## 🛠️ 설정 파일 예시

### `.env` 파일 (권장)
```
NAVER_API_KEY=your_api_key
NAVER_SECRET_KEY=your_secret_key
NAVER_CUSTOMER_ID=your_customer_id
```

### `.gitignore`
```
data/info.csv
.env
*.key
*.secret
```

---

## 📞 문제 발생시

**API Key/Secret 노출 발생시**:
1. 네이버 검색광고 관리자 → API 관리
2. 현재 API Key 삭제 또는 재발급
3. 새로운 Key로 `data/info.csv` 업데이트
4. Git 이력 확인 및 정리

---

**기준**: 🔒 **Zero Tolerance**  
**점검**: 커밋 전 필수  
**상태**: ✅ **현재 안전**

