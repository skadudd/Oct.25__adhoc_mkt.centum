#!/bin/bash

# API 키 읽기
API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

# macOS - openssl 사용
SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_KEY" | cut -d' ' -f2)

echo "🔍 상세 API 응답 분석"
echo "======================================"

echo ""
echo "1️⃣ 요청 정보:"
echo "   URL: https://api.searchad.naver.com/v1/campaigns"
echo "   Method: GET"
echo "   Headers:"
echo "   - X-API-KEY: ${API_KEY:0:20}..."
echo "   - X-CUSTOMER-ID: ${CUSTOMER_ID:0:20}..."
echo "   - X-TIMESTAMP: $TIMESTAMP"
echo "   - X-SIGNATURE: ${SIGNATURE:0:30}..."

echo ""
echo "2️⃣ 전체 응답 (헤더 + 본문):"
echo "   ================================"

curl -v -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1 | head -50

echo "   ================================"
echo ""
echo "3️⃣ JSON 응답만 추출:"

curl -s -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1 | python3 -m json.tool 2>/dev/null || \
curl -s -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1

