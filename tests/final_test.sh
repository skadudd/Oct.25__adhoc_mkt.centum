#!/bin/bash

API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

# 원래 Secret Key (Base64)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

echo "🎯 최종 API 테스트 (Secret Key 사용)"
echo "======================================"

echo ""
echo "1️⃣ 요청 정보:"
echo "   API Key: ${API_KEY:0:30}..."
echo "   Customer ID: $CUSTOMER_ID"
echo "   Secret Key (Base64): ${SECRET_KEY:0:30}..."
echo "   Message: $MESSAGE"

# Secret Key를 사용한 서명 생성 (3가지 방식)

echo ""
echo "2️⃣ 서명 생성 방식 테스트:"

# 방식 1: Secret Key를 그대로 문자열로 사용
echo ""
echo "   방식 1: Secret Key 직접 사용 (문자열)"
SIGNATURE_1=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_KEY" | cut -d' ' -f2)
echo "   Signature: ${SIGNATURE_1:0:30}..."

# 테스트 1
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_1" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")
  
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP $HTTP_CODE - 성공!"
else
    echo "   ❌ HTTP $HTTP_CODE"
fi

# 방식 2: Secret Key Base64 디코딩 후 사용
echo ""
echo "   방식 2: Secret Key Base64 디코딩 후 사용"
SECRET_DECODED=$(echo -n "$SECRET_KEY" | base64 -d | xxd -p)
SIGNATURE_2=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$SECRET_DECODED" | cut -d' ' -f2)
echo "   Signature: ${SIGNATURE_2:0:30}..."

# 테스트 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_2" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")
  
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP $HTTP_CODE - 성공!"
else
    echo "   ❌ HTTP $HTTP_CODE"
fi

# 방식 3: X-SECRET-KEY 헤더 추가
echo ""
echo "   방식 3: X-SECRET-KEY 헤더 추가"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-SECRET-KEY: $SECRET_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE_1" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns")
  
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP $HTTP_CODE - 성공!"
else
    echo "   ❌ HTTP $HTTP_CODE"
fi

echo ""
echo "======================================"
