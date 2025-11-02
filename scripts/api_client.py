"""
네이버 검색광고 API 클라이언트

Naver Search Ads API Docs: https://naver.github.io/searchad-apidoc/#/guides
"""

import requests
import json
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class NaverSearchAdsAPI:
    """
    네이버 검색광고 API 클라이언트
    
    API Endpoint: https://api.searchad.naver.com/v1
    인증: X-API-KEY, X-CUSTOMER-ID, X-TIMESTAMP, X-SIGNATURE (HMAC-SHA256)
    
    주요 기능:
    - 캠페인 조회
    - 키워드 조회
    - 통계 데이터 조회 (일별, 주별, 월별)
    - 광고 성과 지표 수집
    """
    
    def __init__(self, api_key: str, customer_id: str):
        """
        Args:
            api_key: Naver Search Ads API Key (X-API-KEY)
            customer_id: Naver Customer ID (X-CUSTOMER-ID)
        """
        self.api_key = api_key
        self.customer_id = customer_id
        self.base_url = 'https://api.searchad.naver.com/v1'
        self.session = requests.Session()
    
    def _generate_signature(self, timestamp: str, method: str, uri: str, body: str = '') -> str:
        """
        HMAC-SHA256 서명 생성
        
        Args:
            timestamp: Unix timestamp (밀리초)
            method: HTTP 메서드 (GET, POST 등)
            uri: 요청 URI 경로 (/campaigns, /stats 등)
            body: 요청 body (JSON 문자열)
            
        Returns:
            X-Signature 헤더 값
        """
        # 서명 생성 문자열: {method} {uri} {timestamp}
        message = f"{method} {uri} {timestamp}"
        
        if body:
            message = f"{message}\n{body}"
        
        # HMAC-SHA256로 서명 생성
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_headers(self, method: str, uri: str, body: str = '') -> Dict[str, str]:
        """
        API 요청 헤더 생성
        
        Args:
            method: HTTP 메서드
            uri: 요청 URI
            body: 요청 body
            
        Returns:
            헤더 딕셔너리
        """
        timestamp = str(int(time.time() * 1000))  # 현재 시간 (밀리초)
        signature = self._generate_signature(timestamp, method, uri, body)
        
        headers = {
            'X-API-KEY': self.api_key,
            'X-CUSTOMER-ID': self.customer_id,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        API 응답 처리
        
        Args:
            response: requests.Response 객체
            
        Returns:
            응답 JSON 데이터
            
        Raises:
            requests.exceptions.HTTPError: HTTP 에러
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP {response.status_code}")
            print(f"   응답: {response.text}")
            raise requests.exceptions.HTTPError(str(e)) from e
    
    def get_campaigns(self) -> Optional[Dict[str, Any]]:
        """
        캠페인 목록 조회
        
        Returns:
            캠페인 정보 (id, name, status, budget 등)
        """
        endpoint = f'{self.base_url}/campaigns'
        uri = '/campaigns'
        
        try:
            headers = self._get_headers('GET', uri)
            response = requests.get(endpoint, headers=headers, timeout=10)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"❌ 캠페인 조회 실패: {e}")
            return None
    
    def get_ad_groups(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        캠페인별 광고그룹 조회
        
        Args:
            campaign_id: 캠페인 ID
            
        Returns:
            광고그룹 정보
        """
        endpoint = f'{self.base_url}/campaigns/{campaign_id}/adgroups'
        uri = f'/campaigns/{campaign_id}/adgroups'
        
        try:
            headers = self._get_headers('GET', uri)
            response = requests.get(endpoint, headers=headers, timeout=10)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"❌ 광고그룹 조회 실패: {e}")
            return None
    
    def get_keywords(self, campaign_id: int, ad_group_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        키워드 조회
        
        Args:
            campaign_id: 캠페인 ID
            ad_group_id: 광고그룹 ID (선택사항)
            
        Returns:
            키워드 정보 (keyword, status, bid 등)
        """
        if ad_group_id:
            endpoint = f'{self.base_url}/campaigns/{campaign_id}/adgroups/{ad_group_id}/keywords'
            uri = f'/campaigns/{campaign_id}/adgroups/{ad_group_id}/keywords'
        else:
            endpoint = f'{self.base_url}/campaigns/{campaign_id}/keywords'
            uri = f'/campaigns/{campaign_id}/keywords'
        
        try:
            headers = self._get_headers('GET', uri)
            response = requests.get(endpoint, headers=headers, timeout=10)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"❌ 키워드 조회 실패: {e}")
            return None
    
    def get_statistics(
        self,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[int]] = None,
        ad_group_ids: Optional[List[int]] = None,
        keyword_ids: Optional[List[int]] = None,
        time_unit: str = 'DAY'
    ) -> Optional[Dict[str, Any]]:
        """
        통계 데이터 조회
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            campaign_ids: 캠페인 ID 리스트 (선택사항)
            ad_group_ids: 광고그룹 ID 리스트 (선택사항)
            keyword_ids: 키워드 ID 리스트 (선택사항)
            time_unit: 시간 단위 (DAY, WEEK, MONTH) - 기본값: DAY
            
        Returns:
            통계 데이터 (impressions, clicks, cost, conversions 등)
        """
        endpoint = f'{self.base_url}/stats'
        uri = '/stats'
        
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'timeUnit': time_unit,
            'fields': [
                'impressions',
                'clicks',
                'cost',
                'conversions',
                'conversionValue',
                'ctr',
                'cpc',
                'cvr',
                'roas'
            ]
        }
        
        # ID 필터 추가 (선택사항)
        if campaign_ids:
            payload['ids'] = campaign_ids
        if ad_group_ids:
            payload['adgroupIds'] = ad_group_ids
        if keyword_ids:
            payload['keywordIds'] = keyword_ids
        
        body = json.dumps(payload, ensure_ascii=False)
        
        try:
            headers = self._get_headers('POST', uri, body)
            response = requests.post(endpoint, headers=headers, data=body.encode('utf-8'), timeout=10)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            print(f"❌ 통계 조회 실패: {e}")
            return None
    
    def get_daily_statistics(
        self,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        일별 통계 조회 (편의 메서드)
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            campaign_ids: 캠페인 ID 리스트 (선택사항)
            
        Returns:
            일별 통계 데이터
        """
        return self.get_statistics(
            start_date=start_date,
            end_date=end_date,
            campaign_ids=campaign_ids,
            time_unit='DAY'
        )
    
    def get_weekly_statistics(
        self,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        주별 통계 조회 (편의 메서드)
        """
        return self.get_statistics(
            start_date=start_date,
            end_date=end_date,
            campaign_ids=campaign_ids,
            time_unit='WEEK'
        )
    
    def get_monthly_statistics(
        self,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        월별 통계 조회 (편의 메서드)
        """
        return self.get_statistics(
            start_date=start_date,
            end_date=end_date,
            campaign_ids=campaign_ids,
            time_unit='MONTH'
        )


# 사용 예시
if __name__ == "__main__":
    # 초기화
    api = NaverSearchAdsAPI(
        api_key="YOUR_API_KEY",
        customer_id="YOUR_CUSTOMER_ID"
    )
    
    # 캠페인 조회
    campaigns = api.get_campaigns()
    print("Campaigns:", json.dumps(campaigns, indent=2, ensure_ascii=False))
    
    # 통계 조회
    stats = api.get_daily_statistics("2025-10-01", "2025-10-31")
    print("Statistics:", json.dumps(stats, indent=2, ensure_ascii=False))
