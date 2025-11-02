#!/bin/bash

API_KEY="YOUR_API_KEY_HERE"
CUSTOMER_ID="YOUR_CUSTOMER_ID_HERE"

echo "🔬 종합 API 인증 테스트"
echo "=================================================="

# 테스트 1: X-API-KEY만
echo ""
echo "1️⃣ X-API-KEY만 사용"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 2: X-API-KEY + X-Customer
echo ""
echo "2️⃣ X-API-KEY + X-Customer"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 3: Basic 인증 (API-KEY:CUSTOMER-ID)
echo ""
echo "3️⃣ Basic 인증 (API-KEY:CUSTOMER-ID)"
BASIC_AUTH=$(echo -n "$API_KEY:$CUSTOMER_ID" | base64)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "Authorization: Basic $BASIC_AUTH" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 4: Basic 인증 (API-KEY:SECRET-KEY)
echo ""
echo "4️⃣ Basic 인증 (API-KEY:SECRET-KEY)"
BASIC_AUTH=$(echo -n "$API_KEY:$SECRET_KEY" | base64)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "Authorization: Basic $BASIC_AUTH" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 5: Bearer 토큰 (API Key)
echo ""
echo "5️⃣ Bearer 토큰 (API Key)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "Authorization: Bearer $API_KEY" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 6: 쿼리 파라미터로 인증
echo ""
echo "6️⃣ 쿼리 파라미터 (api_key)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  "https://api.searchad.naver.com/v1/campaigns?api_key=$API_KEY&customer=$CUSTOMER_ID")
echo "   HTTP $HTTP_CODE"

# 테스트 7: POST 메서드 시도
echo ""
echo "7️⃣ POST 메서드"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")
echo "   HTTP $HTTP_CODE"

# 테스트 8: /stat 엔드포인트 (POST)
echo ""
echo "8️⃣ /stat 엔드포인트 (POST)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "Content-Type: application/json" \
  -d '{"startDate":"2025-10-01","endDate":"2025-10-31"}' \
  "https://api.searchad.naver.com/v1/stat")
echo "   HTTP $HTTP_CODE"

echo ""
echo "=================================================="
echo "✅ 테스트 완료"
