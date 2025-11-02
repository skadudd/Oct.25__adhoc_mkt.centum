"""
네이버 검색광고 API 테스트 스크립트
"""

import requests
import json
import hmac
import hashlib
import time
import sys
from pathlib import Path

# API 키 로드
sys.path.insert(0, str(Path(__file__).parent.parent))
import pandas as pd

api_info = pd.read_csv('../data/info.csv')
api_key = api_info[api_info['media'] == 'nsa']['key'].values[0]
customer_id = api_info[api_info['media'] == 'nsa']['scr'].values[0]

print("🔍 네이버 검색광고 API 테스트")
print("=" * 60)

# 1️⃣ API 정보 출력
print(f"\n1️⃣ API 정보:")
print(f"   - API Key (앞 30자): {api_key[:30]}...")
print(f"   - Customer ID (앞 30자): {customer_id[:30]}...")

# 2️⃣ 헤더 생성 테스트
print(f"\n2️⃣ 헤더 생성 테스트:")

timestamp = str(int(time.time() * 1000))
method = 'GET'
uri = '/campaigns'

# 서명 생성
message = f"{method} {uri} {timestamp}"
signature = hmac.new(
    api_key.encode('utf-8'),
    message.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"   - Timestamp: {timestamp}")
print(f"   - Method: {method}")
print(f"   - URI: {uri}")
print(f"   - Message: {message}")
print(f"   - Signature (앞 30자): {signature[:30]}...")

# 3️⃣ 다양한 헤더 조합 테스트
print(f"\n3️⃣ 헤더 조합 테스트:")

headers_options = [
    {
        "name": "Option 1: X-CUSTOMER-ID",
        "headers": {
            'X-API-KEY': api_key,
            'X-CUSTOMER-ID': customer_id,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
    },
    {
        "name": "Option 2: X-Customer",
        "headers": {
            'X-API-KEY': api_key,
            'X-Customer': customer_id,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
    },
    {
        "name": "Option 3: Authorization Bearer",
        "headers": {
            'Authorization': f'Bearer {api_key}',
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
    }
]

base_url = 'https://api.searchad.naver.com/v1'

for option in headers_options:
    print(f"\n   📌 {option['name']}:")
    
    try:
        print(f"      헤더: {list(option['headers'].keys())}")
        
        response = requests.get(
            f'{base_url}/campaigns',
            headers=option['headers'],
            timeout=5
        )
        
        print(f"      상태: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print(f"      ✅ 성공!")
            data = response.json()
            print(f"      응답 샘플: {str(data)[:100]}...")
        else:
            print(f"      ❌ 실패")
            print(f"      응답: {response.text[:200]}")
    
    except Exception as e:
        print(f"      ❌ 에러: {str(e)[:100]}")

# 4️⃣ 다양한 API 엔드포인트 테스트
print(f"\n4️⃣ 엔드포인트 테스트:")

endpoints = [
    '/campaigns',
    '/customer',
    '/v1/campaigns',
    '/stat',
    '/stats'
]

headers_default = {
    'X-API-KEY': api_key,
    'X-CUSTOMER-ID': customer_id,
    'X-TIMESTAMP': timestamp,
    'X-SIGNATURE': signature,
    'Content-Type': 'application/json'
}

for endpoint in endpoints:
    try:
        url = f'{base_url}{endpoint}' if not endpoint.startswith('/v1') else f'https://api.searchad.naver.com{endpoint}'
        response = requests.get(url, headers=headers_default, timeout=5)
        status = "✅" if response.status_code < 400 else "❌"
        print(f"   {status} {endpoint}: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ {endpoint}: {str(e)[:50]}")

print("\n" + "=" * 60)
print("테스트 완료!")
