#!/bin/bash

API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_KEY" | cut -d' ' -f2)

echo "📊 API 응답만 출력 (상세 버전)"
echo ""

curl -s -i -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns"
