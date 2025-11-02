"""
Jupyter Notebook용 Nevada API 테스트 스크립트
"""

import sys
sys.path.insert(0, '../scripts')

from api_client_nevada import NaverSearchAdsConnector
import pandas as pd
import json

print("🔍 Nevada 기반 API 테스트")
print("=" * 70)

# API 정보 로드
api_info = pd.read_csv('../data/info.csv')
api_key = api_info[api_info['media'] == 'nsa']['key'].values[0]
customer_id = int(api_info[api_info['media'] == 'nsa']['scr'].values[0])

print("\n📋 API 정보:")
print(f"   - API Key: {api_key[:30]}...")
print(f"   - Customer ID: {customer_id}")
print(f"   - Base URL: https://api.naver.com")

# Connector 생성
conn = NaverSearchAdsConnector(
    'https://api.naver.com',
    api_key,
    secret_key,
    customer_id
)

# 테스트 1: 현재 시간 조회
print("\n" + "=" * 70)
print("🕐 Test 1: 현재 시간 조회")
print("=" * 70)
result = conn.get_datetime()
if result:
    print("\n✅ 성공!")
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print("\n❌ 실패")

# 테스트 2: 캠페인 목록 조회
print("\n" + "=" * 70)
print("📋 Test 2: 캠페인 목록 조회")
print("=" * 70)
result = conn.get_campaigns()
if result:
    print("\n✅ 성공!")
    if isinstance(result, dict) and 'campaigns' in result:
        campaigns_df = pd.DataFrame(result['campaigns'])
        print(f"\n총 {len(campaigns_df)}개 캠페인:")
        print(campaigns_df[['id', 'name', 'status']].head(10))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
else:
    print("\n❌ 실패")

print("\n" + "=" * 70)
print("✅ 테스트 완료")
