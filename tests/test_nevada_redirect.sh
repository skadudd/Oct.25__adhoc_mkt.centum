#!/bin/bash

API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

echo "🔄 리다이렉트 확인"
echo "======================================"

# 리다이렉트 따라가기 (-L 옵션)
PATH="/searchad/apiservice.naver"
TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
MESSAGE="${METHOD} ${PATH} ${TIMESTAMP}"
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)

echo ""
echo "1️⃣ 리다이렉트 따라가기 (Location 헤더 확인)"

RESPONSE=$(curl -s -i -L -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-Timestamp: $TIMESTAMP" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.naver.com${PATH}" 2>&1)

echo "$RESPONSE" | head -20
echo ""
echo "응답 본문 (처음 300자):"
echo "$RESPONSE" | tail -n +13 | head -c 300

echo ""
echo "======================================"
