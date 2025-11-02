#!/bin/bash

# API 정보 로드
API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

echo "🔍 Nevada 방식 API 테스트"
echo "======================================"
echo ""
echo "📋 API 정보:"
echo "   Base URL: https://api.naver.com"
echo "   API Key: ${API_KEY:0:30}..."
echo "   Customer ID: $CUSTOMER_ID"
echo ""

# 경로 설정 (nevada 방식)
PATH_TIME="/searchad/apiservice.naver"
PATH_CAMPAIGNS="/searchad/campaigns.naver"

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"

# 테스트 1: 현재 시간 조회
echo "1️⃣ 현재 시간 조회 테스트"
echo "   경로: $PATH_TIME"

MESSAGE="${METHOD} ${PATH_TIME} ${TIMESTAMP}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)

echo "   요청 중..."
RESPONSE=$(curl -s -i -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-Timestamp: $TIMESTAMP" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.naver.com${PATH_TIME}" 2>&1)

HTTP_STATUS=$(echo "$RESPONSE" | head -1)
echo "   응답: $HTTP_STATUS"

if echo "$HTTP_STATUS" | grep -q "200"; then
    echo "   ✅ 성공!"
    echo "$RESPONSE" | tail -n +13 | head -c 300
    echo ""
else
    echo "   ❌ 실패"
fi

# 테스트 2: 캠페인 목록 조회
echo ""
echo "2️⃣ 캠페인 목록 조회 테스트"
echo "   경로: $PATH_CAMPAIGNS"

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
MESSAGE="${METHOD} ${PATH_CAMPAIGNS} ${TIMESTAMP}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)

echo "   요청 중..."
RESPONSE=$(curl -s -i -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-Timestamp: $TIMESTAMP" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.naver.com${PATH_CAMPAIGNS}" 2>&1)

HTTP_STATUS=$(echo "$RESPONSE" | head -1)
echo "   응답: $HTTP_STATUS"

if echo "$HTTP_STATUS" | grep -q "200"; then
    echo "   ✅ 성공!"
    echo "$RESPONSE" | tail -n +13 | head -c 300
    echo ""
else
    echo "   ❌ 실패"
    echo "$RESPONSE" | tail -n +13 | head -c 200
fi

echo ""
echo "======================================"
