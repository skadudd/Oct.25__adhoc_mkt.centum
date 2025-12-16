#!/usr/bin/env python3
"""
베이스 스크래퍼 클래스
모든 스크래퍼 모듈의 공통 인터페이스
"""

import os
import json
import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod
from playwright.async_api import Page


class BaseScraper(ABC):
    """모든 스크래퍼의 베이스 클래스"""
    
    def __init__(self, username: str, password: str, start_date: str = None, end_date: str = None, output_base_dir: str = "data/naverplace"):
        self.username = username
        self.password = password
        self.start_date = start_date
        self.end_date = end_date
        self.output_base_dir = output_base_dir
        self.network_responses = []
    
    @abstractmethod
    async def scrape(self, page: Page) -> dict:
        """
        데이터 스크래핑 메인 메서드
        각 모듈에서 구현해야 함
        
        Args:
            page: Playwright Page 객체
            
        Returns:
            dict: 스크래핑된 데이터
        """
        pass
    
    @abstractmethod
    def get_module_name(self) -> str:
        """
        모듈 이름 반환
        
        Returns:
            str: 모듈 이름 (예: "place_statistics")
        """
        pass
    
    def get_output_dir(self) -> str:
        """
        출력 디렉토리 경로 반환
        
        Returns:
            str: 출력 디렉토리 경로
        """
        module_name = self.get_module_name()
        output_dir = os.path.join(self.output_base_dir, module_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    async def save_results(self, data: dict):
        """
        결과를 파일로 저장
        
        Args:
            data: 저장할 데이터 딕셔너리
        """
        output_dir = self.get_output_dir()
        module_name = self.get_module_name()
        
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
        date_suffix = ""
        if self.start_date and self.end_date:
            start_str = self.start_date.replace("-", "")
            end_str = self.end_date.replace("-", "")
            date_suffix = f"__{start_str}_{end_str}"
        
        # CSV 저장 (다양한 데이터 키 지원)
        csv_data = None
        print(f"\n[Save Results] Checking data keys: {list(data.keys())}")
        
        if data.get("hover_data"):
            csv_data = data["hover_data"]
            print(f"  ✓ Found hover_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        elif data.get("time_based_data"):
            csv_data = data["time_based_data"]
            print(f"  ✓ Found time_based_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        elif data.get("channel_data"):
            csv_data = data["channel_data"]
            print(f"  ✓ Found channel_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        elif data.get("segment_data"):
            csv_data = data["segment_data"]
            print(f"  ✓ Found segment_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        elif data.get("call_statistics_data") is not None:
            csv_data = data["call_statistics_data"]
            print(f"  ✓ Found call_statistics_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
            if isinstance(csv_data, list):
                if len(csv_data) > 0:
                    print(f"    First row sample: {csv_data[0]}")
                else:
                    print(f"    ⚠ Warning: call_statistics_data is empty list")
            else:
                print(f"    ⚠ Warning: call_statistics_data is not a list: {type(csv_data)}")
        elif data.get("top_media_data"):
            csv_data = data["top_media_data"]
            print(f"  ✓ Found top_media_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        elif data.get("top_keyword_data"):
            csv_data = data["top_keyword_data"]
            print(f"  ✓ Found top_keyword_data: {len(csv_data) if isinstance(csv_data, list) else 'N/A'} items")
        else:
            print(f"  ⚠ No CSV data key found in data")
        
        # csv_data가 None이 아니고 리스트인 경우 CSV 저장 (빈 리스트도 포함)
        if csv_data is not None and isinstance(csv_data, list):
            print(f"  [CSV Save] csv_data type: {type(csv_data)}, length: {len(csv_data)}")
            
            try:
                # event_dt 컬럼 추가 (YYYY-MM-DD 형식)
                # start_date와 end_date가 같으면 그 날짜 사용, 다르면 start_date 사용
                target_date = self.start_date if self.start_date else self.end_date
                
                # 각 행에 event_dt 추가
                for row in csv_data:
                    if isinstance(row, dict):
                        row["event_dt"] = target_date
                    else:
                        print(f"  ⚠ Warning: row is not a dict: {type(row)}, value: {row}")
                
                df = pd.DataFrame(csv_data)
                print(f"  [DataFrame] Created DataFrame with {len(df)} rows, {len(df.columns)} columns")
                if len(df.columns) > 0:
                    print(f"    Columns: {list(df.columns)}")
                
                # CSV 파일명: 모듈명__시작일_종료일.csv
                csv_filename = f"{module_name}{date_suffix}.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"✓ CSV saved: {csv_path}")
                
                # 데이터 요약 출력
                if len(csv_data) > 0:
                    self._print_data_summary(csv_data)
                else:
                    print(f"  ⚠ Warning: CSV file created but contains no data rows")
            except Exception as e:
                print(f"  ✗ Error saving CSV: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  ⚠ No CSV data to save (csv_data is {csv_data}, type: {type(csv_data)})")
        
        # JSON 저장 (CSV와 동일한 파일명 형식 사용)
        json_filename = f"{module_name}{date_suffix}.json"
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON saved: {json_path}")
    
    def _print_data_summary(self, data: list):
        """
        데이터 요약 정보 출력
        
        Args:
            data: 데이터 리스트
        """
        if not data:
            return
        
        # 시간별 데이터인 경우
        if isinstance(data[0], dict) and "hour" in data[0]:
            valid_data = [d for d in data if d.get("count") is not None]
            if valid_data:
                print(f"\n  Data Summary:")
                print(f"    - Total time points with data: {len(valid_data)}")
                hours = [d['hour'] for d in valid_data if d.get('hour') is not None]
                if hours:
                    print(f"    - Hour range: {min(hours)}시 ~ {max(hours)}시")
                counts = [d['count'] for d in valid_data if d.get('count') is not None]
                if counts:
                    total_count = sum(counts)
                    print(f"    - Total count: {total_count}회")

