#!/bin/bash

API_KEY="YOUR_API_KEY_HERE"
CUSTOMER_ID="YOUR_CUSTOMER_ID_HERE"

echo "🔍 Nevada 방식 최종 테스트 (경로 변형)"
echo "=================================================="

# 테스트 1: /searchad/apiservice.naver
echo ""
echo "1️⃣ Base URL: https://api.naver.com"
echo "   경로: /searchad/apiservice.naver"
curl -s -i "https://api.naver.com/searchad/apiservice.naver" | head -10

# 테스트 2: /searchad/campaigns
echo ""
echo "2️⃣ 경로: /searchad/campaigns.naver"
curl -s -i "https://api.naver.com/searchad/campaigns.naver" | head -10

# 테스트 3: /v1/campaigns (v1 경로 시도)
echo ""
echo "3️⃣ 경로: /v1/campaigns"
curl -s -i "https://api.naver.com/v1/campaigns" | head -10

# 테스트 4: https://api.searchad.naver.com/v1/campaigns
echo ""
echo "4️⃣ Base URL: https://api.searchad.naver.com"
echo "   경로: /v1/campaigns"
curl -s -i "https://api.searchad.naver.com/v1/campaigns" | head -10

echo ""
echo "=================================================="
