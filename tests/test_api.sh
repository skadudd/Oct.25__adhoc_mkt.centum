#!/bin/bash

# API 키 읽기
API_KEY=$(grep "^nsa," ./data/info.csv | cut -d',' -f2)
CUSTOMER_ID=$(grep "^nsa," ./data/info.csv | cut -d',' -f3)

echo "🔍 네이버 검색광고 API curl 테스트"
echo "======================================"

# 1. API 정보 출력
echo ""
echo "1️⃣ API 정보:"
echo "   API Key (앞 20자): ${API_KEY:0:20}..."
echo "   Customer ID (앞 20자): ${CUSTOMER_ID:0:20}..."

# 2. 기본 정보 생성
TIMESTAMP=$(date +%s%N | sed 's/000$//' | cut -c1-13)
METHOD="GET"
URI="/campaigns"
MESSAGE="${METHOD} ${URI} ${TIMESTAMP}"

echo ""
echo "2️⃣ 서명 정보:"
echo "   Timestamp: $TIMESTAMP"
echo "   Method: $METHOD"
echo "   URI: $URI"
echo "   Message: $MESSAGE"

# 3. 서명 생성 (macOS - openssl 사용)
if [[ "$OSTYPE" == "darwin"* ]]; then
    SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_KEY" | cut -d' ' -f2)
else
    SIGNATURE=$(echo -n "$MESSAGE" | openssl dgst -sha256 -hmac "$API_KEY" | awk '{print $NF}')
fi

echo "   Signature (앞 30자): ${SIGNATURE:0:30}..."

# 4. 헤더 조합 1: X-CUSTOMER-ID
echo ""
echo "3️⃣ 헤더 조합 테스트:"
echo ""
echo "   📌 Option 1: X-CUSTOMER-ID"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "      상태: HTTP $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ 성공!"
    echo "      응답 (앞 150자): ${BODY:0:150}..."
else
    echo "      ❌ 실패"
    echo "      응답 (앞 200자): ${BODY:0:200}..."
fi

# 5. 헤더 조합 2: X-Customer (하이픈 제거)
echo ""
echo "   📌 Option 2: X-Customer"

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  -H "X-API-KEY: $API_KEY" \
  -H "X-Customer: $CUSTOMER_ID" \
  -H "X-TIMESTAMP: $TIMESTAMP" \
  -H "X-SIGNATURE: $SIGNATURE" \
  -H "Content-Type: application/json" \
  "https://api.searchad.naver.com/v1/campaigns" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "      상태: HTTP $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "      ✅ 성공!"
    echo "      응답 (앞 150자): ${BODY:0:150}..."
else
    echo "      ❌ 실패"
fi

# 6. 다양한 엔드포인트 테스트
echo ""
echo "4️⃣ 엔드포인트 테스트:"

for endpoint in "/campaigns" "/stats" "/keywords"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
      -H "X-API-KEY: $API_KEY" \
      -H "X-CUSTOMER-ID: $CUSTOMER_ID" \
      -H "X-TIMESTAMP: $TIMESTAMP" \
      -H "X-SIGNATURE: $SIGNATURE" \
      -H "Content-Type: application/json" \
      "https://api.searchad.naver.com/v1$endpoint" 2>&1)
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        echo "   ✅ $endpoint: HTTP $HTTP_CODE"
    else
        echo "   ❌ $endpoint: HTTP $HTTP_CODE"
    fi
done

echo ""
echo "======================================"
echo "테스트 완료!"
