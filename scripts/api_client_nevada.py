"""
네이버 검색광고 API 클라이언트 (python_nevada 기반)

참고: https://github.com/taegyumin/python_nevada
발견: api.naver.com은 api.searchad.naver.com으로 리다이렉트됨
"""

import requests
import json
import hmac
import hashlib
import time
from typing import Dict, Optional, Any


class NaverSearchAdsConnector:
    """
    네이버 검색광고 API 커넥터 (python_nevada 방식)
    
    Corrected API Specification:
    - Base URL: https://api.searchad.naver.com (api.naver.com은 리다이렉트)
    - 경로 형식: /searchad/{resource}.naver
    - 인증: X-API-KEY, X-Customer, X-Timestamp, X-Signature
    
    예시:
    - https://api.searchad.naver.com/searchad/apiservice.naver (시간 조회)
    - https://api.searchad.naver.com/searchad/campaigns.naver (캠페인 조회)
    """
    
    def __init__(self, api_key: str, secret_key: str, customer_id: int):
        """
        Args:
            api_key: 액세스라이선스
            secret_key: 비밀키
            customer_id: 고객 ID (숫자)
        """
        self.base_url = 'https://api.searchad.naver.com'  # ✅ 올바른 Base URL
        self.api_key = api_key
        self.secret_key = secret_key
        self.customer_id = str(customer_id)
    
    def _generate_signature(self, method: str, path: str, timestamp: str) -> str:
        """
        HMAC-SHA256 서명 생성
        
        서명 메시지: {METHOD} {PATH} {TIMESTAMP}
        예: GET /searchad/apiservice.naver 1730558400123
        """
        message = f"{method} {path} {timestamp}"
        secret_bytes = self.secret_key.encode('utf-8')
        signature = hmac.new(
            secret_bytes,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, method: str, path: str) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(method, path, timestamp)
        
        headers = {
            'X-API-KEY': self.api_key,
            'X-Customer': self.customer_id,
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'Content-Type': 'application/json'
        }
        return headers
    
    def _request(self, method: str, path: str, body: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """API 요청 실행"""
        url = f"{self.base_url}{path}"
        headers = self._get_headers(method, path)
        
        print(f"📡 {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(
                    url, headers=headers,
                    data=body.encode('utf-8') if body else None,
                    timeout=10
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"   HTTP {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   응답: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"   ❌ 에러: {e}")
            return None
    
    def get_datetime(self) -> Optional[str]:
        """현재 시간 조회 (테스트)"""
        print("\n🕐 현재 시간 조회:")
        return self._request('GET', '/searchad/apiservice.naver')
    
    def get_campaigns(self) -> Optional[Dict[str, Any]]:
        """캠페인 목록 조회"""
        print("\n📋 캠페인 목록 조회:")
        return self._request('GET', '/searchad/campaigns.naver')
    
    def get_keywords(self, campaign_id: int, ad_group_id: int) -> Optional[Dict[str, Any]]:
        """키워드 목록 조회"""
        print(f"\n🔑 키워드 조회 (Campaign={campaign_id}, AdGroup={ad_group_id}):")
        return self._request(
            'GET',
            f'/searchad/campaigns/{campaign_id}/adgroups/{ad_group_id}/keywords.naver'
        )


if __name__ == "__main__":
    import pandas as pd
    
    api_info = pd.read_csv('../data/info.csv')
    api_key = api_info[api_info['media'] == 'nsa']['key'].values[0]
    customer_id = int(api_info[api_info['media'] == 'nsa']['scr'].values[0])
    
    print("🔍 Nevada 방식 API 테스트 (수정됨)")
    print("=" * 60)
    
    conn = NaverSearchAdsConnector(api_key, secret_key, customer_id)
    
    # 테스트 1: 현재 시간 조회
    result = conn.get_datetime()
    if result:
        print(f"✅ 성공!\n{json.dumps(result, indent=2)[:300]}")
    else:
        print("❌ 실패")
    
    # 테스트 2: 캠페인 목록 조회
    print("\n" + "=" * 60)
    result = conn.get_campaigns()
    if result:
        print(f"✅ 성공!\n{json.dumps(result, indent=2)[:300]}")
    else:
        print("❌ 실패")
