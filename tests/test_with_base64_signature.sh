#!/bin/bash

API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
SECRET_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

echo "🔍 Base64 인코딩된 서명을 사용한 인증 테스트"
echo "======================================"

echo ""
echo "1️⃣ 요청 정보:"
echo "   Timestamp: $TIMESTAMP"
echo "   Message: $MESSAGE"

# Secret Key를 바로 사용한 서명 생성 (Hex)
SIGNATURE_HEX=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)
echo "   Signature (Hex): ${SIGNATURE_HEX:0:30}..."

# Hex를 Base64로 변환
SIGNATURE_B64=$(echo -n "$SIGNATURE_HEX" | xxd -r -p | base64)
echo "   Signature (Base64): ${SIGNATURE_B64:0:30}..."

# 테스트 1: Hex 서명 (현재까지의 방식)
echo ""
echo "2️⃣ Option 1: Hex 서명 (현재)"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_HEX" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

echo "   상태: HTTP $HTTP_CODE"

# 테스트 2: Base64 서명
echo ""
echo "3️⃣ Option 2: Base64 서명 ⭐"

RESPONSE=$(curl -s -i -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_B64" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1)

echo "$RESPONSE" | head -15

# 테스트 3: X-Customer 헤더 포함 (Hex)
echo ""
echo "4️⃣ Option 3: X-Customer 헤더 포함 (Hex 서명)"

CUSTOMER_ID="1"  # 테스트용 기본값
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_HEX" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

echo "   상태: HTTP $HTTP_CODE"

# 테스트 4: X-Customer 헤더 포함 (Base64)
echo ""
echo "5️⃣ Option 4: X-Customer 헤더 포함 (Base64 서명) ⭐"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_B64" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")

echo "   상태: HTTP $HTTP_CODE"

echo ""
echo "======================================"
