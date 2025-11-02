"""
네이버 검색광고 API 클라이언트 v2 (수정 버전)

참고: https://naver.github.io/searchad-apidoc/#/guides

인증 방식:
- X-API-KEY: 액세스라이선스
- X-SECRET-KEY: 비밀키 (또는 서명 생성에 사용)
"""

import requests
import json
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any


class NaverSearchAdsAPI:
    """
    네이버 검색광고 API 클라이언트 v2
    """
    
    def __init__(self, api_key: str, secret_key: str):
        """
        Args:
            api_key: 액세스라이선스 (X-API-KEY)
            secret_key: 비밀키 (X-SECRET-KEY)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://api.searchad.naver.com/v1'
    
    def _generate_signature(self, timestamp: str, method: str, uri: str, body: str = '') -> str:
        """
        HMAC-SHA256 서명 생성
        
        Args:
            timestamp: Unix timestamp (밀리초)
            method: HTTP 메서드 (GET, POST 등)
            uri: 요청 URI 경로
            body: 요청 body
            
        Returns:
            X-Signature 헤더 값
        """
        # 서명 생성: {METHOD} {URI} {TIMESTAMP}
        message = f"{method} {uri} {timestamp}"
        
        if body:
            message = f"{message}\n{body}"
        
        # Secret Key를 바로 사용하거나, 디코딩해서 사용
        # 네이버 API는 Secret Key를 바로 사용하는 경우가 많음
        try:
            # Secret Key가 Base64라면 디코딩
            import base64
            secret_bytes = base64.b64decode(self.secret_key)
        except:
            # 일반 문자열이면 그대로 사용
            secret_bytes = self.secret_key.encode('utf-8')
        
        signature = hmac.new(
            secret_bytes,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_headers(self, method: str, uri: str, body: str = '') -> Dict[str, str]:
        """
        API 요청 헤더 생성
        """
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, uri, body)
        
        headers = {
            'X-API-KEY': self.api_key,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def get_campaigns(self) -> Optional[Dict[str, Any]]:
        """캠페인 목록 조회"""
        endpoint = f'{self.base_url}/campaigns'
        uri = '/campaigns'
        
        try:
            headers = self._get_headers('GET', uri)
            
            print(f"📊 요청 정보:")
            print(f"   URL: {endpoint}")
            print(f"   헤더: {list(headers.keys())}")
            
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            print(f"   응답: HTTP {response.status_code}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 캠페인 조회 실패: {e}")
            if hasattr(e.response, 'text'):
                print(f"   응답 본문: {e.response.text[:200]}")
            return None


if __name__ == "__main__":
    import pandas as pd
    
    api_info = pd.read_csv('../data/info.csv')
    api_key = api_info[api_info['media'] == 'nsa']['key'].values[0]
    secret_key = api_info[api_info['media'] == 'nsa']['scr'].values[0]
    
    print("🔍 네이버 검색광고 API v2 테스트")
    print("=" * 60)
    
    api = NaverSearchAdsAPI(api_key, secret_key)
    result = api.get_campaigns()
    
    if result:
        print("\n✅ 성공!")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    else:
        print("\n❌ 실패")
