#!/bin/bash

# API 키 읽기
API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
SECRET_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

echo "🔍 Secret Key를 사용한 API 인증 테스트"
echo "======================================"

echo ""
echo "1️⃣ 요청 정보:"
echo "   API Key (앞 20자): ${API_KEY:0:20}..."
echo "   Secret Key (앞 20자): ${SECRET_KEY:0:20}..."
echo "   Timestamp: $TIMESTAMP"
echo "   Message: $MESSAGE"

# Secret Key를 바로 사용한 서명 생성
echo ""
echo "2️⃣ 서명 생성 (Secret Key 직접 사용):"

# macOS에서 openssl 사용
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)
echo "   Signature: ${SIGNATURE:0:30}..."

# 헤더 조합 1: Secret Key를 그대로 사용
echo ""
echo "3️⃣ Option 1: Secret Key 직접 사용"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "   상태: HTTP $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 성공!"
    echo "   응답 (앞 200자): ${BODY:0:200}..."
else
    echo "   ❌ 실패"
    if [ ! -z "$BODY" ]; then
        echo "   응답: ${BODY:0:200}..."
    fi
fi

# 헤더 조합 2: Secret Key를 헤더로 추가
echo ""
echo "4️⃣ Option 2: X-SECRET-KEY 헤더 추가"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-SECRET-KEY: $SECRET_KEY" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "   상태: HTTP $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 성공!"
    echo "   응답 (앞 200자): ${BODY:0:200}..."
else
    echo "   ❌ 실패"
fi

# 헤더 조합 3: 기본 인증 (API Key와 Secret Key)
echo ""
echo "5️⃣ Option 3: Basic 인증 시도"

CREDENTIALS=$(echo -n "$API_KEY:$SECRET_KEY" | base64)
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "Authorization: Basic $CREDENTIALS" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "   상태: HTTP $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 성공!"
else
    echo "   ❌ 실패"
fi

echo ""
echo "======================================"
