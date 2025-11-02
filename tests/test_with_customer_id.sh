#!/bin/bash

API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

echo "🔍 Customer ID를 사용한 API 테스트"
echo "======================================"

echo ""
echo "1️⃣ 요청 정보:"
echo "   API Key (앞 30자): ${API_KEY:0:30}..."
echo "   Customer ID: $CUSTOMER_ID"
echo "   Timestamp: $TIMESTAMP"
echo "   Message: $MESSAGE"

# Secret Key를 바로 사용한 서명 생성
SIGNATURE_HEX=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_KEY" | cut -d' ' -f2)
echo "   Signature (Hex): ${SIGNATURE_HEX:0:30}..."

# 테스트 1: X-Customer 헤더 + Hex 서명
echo ""
echo "2️⃣ Option 1: X-Customer + Hex 서명"

RESPONSE=$(curl -s -i -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_HEX" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1)

HTTP_STATUS=$(echo "$RESPONSE" | head -1)
echo "   응답: $HTTP_STATUS"

if echo "$HTTP_STATUS" | grep -q "200"; then
    echo "   ✅ 성공!"
    echo ""
    echo "3️⃣ 응답 데이터 (처음 500자):"
    echo "$RESPONSE" | tail -n +13 | head -c 500
    echo "..."
else
    echo "   ❌ 실패"
    # Base64 서명도 시도
    echo ""
    echo "3️⃣ Option 2: X-Customer + Base64 서명 시도"
    
    SIGNATURE_B64=$(echo -n "$SIGNATURE_HEX" | xxd -r -p | base64)
    
    RESPONSE=$(curl -s -i -X GET \
      -H "X-API-KEY: $API_KEY" \
      -H "X-Customer: $CUSTOMER_ID" \
      -H "X-TIMESTAMP: $TIMESTAMP" \
      -H "X-SIGNATURE: $SIGNATURE_B64" \
      -H "Content-Type: application/json" \
      "https://api.searchad.naver.com/v1/campaigns" 2>&1)
    
    HTTP_STATUS=$(echo "$RESPONSE" | head -1)
    echo "   응답: $HTTP_STATUS"
    
    if echo "$HTTP_STATUS" | grep -q "200"; then
        echo "   ✅ 성공!"
    else
        echo "   ❌ 실패"
    fi
fi

echo ""
echo "======================================"
