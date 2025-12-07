#!/usr/bin/env python3
"""
네이버 스마트플레이스 플레이스 유입 채널 데이터 스크래퍼 모듈
"""

import asyncio
import os
import json
import pandas as pd
from datetime import datetime
from playwright.async_api import Page
from .base_scraper import BaseScraper


class PlaceInflowChannelScraper(BaseScraper):
    """플레이스 유입 채널 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-11-15", end_date: str = "2025-11-15", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성 (place_hourly_inflow_graph와 동일한 페이지)
        self.stats_url = (
            f"https://new.smartplace.naver.com/bizes/place/5921383/statistics"
            f"?bookingBusinessId=603738&endDate={end_date}&menu=place"
            f"&placeTab=inflow&startDate={start_date}&term=daily"
        )
    
    def get_module_name(self) -> str:
        return "place_inflow_channel"
    
    async def extract_channel_data(self, page: Page) -> list:
        """유입 채널 데이터 추출"""
        print("\n[Data Extraction] Extracting inflow channel data...")
        
        channel_data = []
        
        try:
            # JavaScript로 직접 리스트 아이템 찾기 (실제 HTML 구조에 맞춤)
            js_result = await page.evaluate(
                """
                () => {
                    const result = {
                        items_found: 0,
                        data: []
                    };
                    
                    // 리스트 아이템 직접 찾기 (실제 클래스명 사용)
                    const items = document.querySelectorAll('li.Statistics_inflow_list_item__EjiuR');
                    result.items_found = items.length;
                    
                    // 각 항목에서 데이터 추출
                    for (let item of items) {
                        let channel = null;
                        let ratio = null;
                        
                        // channel 추출
                        const channelEl = item.querySelector('span.Statistics_name__M29yR');
                        if (channelEl) {
                            channel = channelEl.innerText || channelEl.textContent;
                            channel = channel ? channel.trim() : null;
                        }
                        
                        // ratio 추출
                        const ratioEl = item.querySelector('span.Statistics_percent__5Tb06');
                        if (ratioEl) {
                            let ratioText = ratioEl.innerText || ratioEl.textContent;
                            if (ratioText) {
                                ratioText = ratioText.trim();
                                ratio = ratioText.replace('%', '').replace('％', '').trim();
                            }
                        }
                        
                        if (channel) {
                            result.data.push({
                                channel: channel,
                                ratio: ratio
                            });
                        }
                    }
                    
                    return result;
                }
                """
            )
            
            print(f"  Found {js_result.get('items_found', 0)} list items")
            
            if js_result.get('data'):
                channel_data = js_result['data']
                print(f"  ✓ Extracted {len(channel_data)} channel items")
                for i, item in enumerate(channel_data, 1):
                    print(f"    {i}. {item.get('channel')} - {item.get('ratio')}%")
            else:
                print("  ⚠ No data extracted")
                
                # Playwright 방식으로 재시도
                print("  Trying Playwright selectors...")
                items = await page.query_selector_all("li.Statistics_inflow_list_item__EjiuR")
                print(f"  Found {len(items)} items via Playwright")
                
                for i, item in enumerate(items, 1):
                    try:
                        # channel 추출
                        channel_element = await item.query_selector("span.Statistics_name__M29yR")
                        channel = None
                        if channel_element:
                            channel = await channel_element.inner_text()
                            channel = channel.strip() if channel else None
                        
                        # ratio 추출
                        ratio_element = await item.query_selector("span.Statistics_percent__5Tb06")
                        ratio = None
                        if ratio_element:
                            ratio_text = await ratio_element.inner_text()
                            ratio_text = ratio_text.strip() if ratio_text else None
                            if ratio_text:
                                ratio = ratio_text.replace("%", "").replace("％", "").strip()
                        
                        if channel:
                            channel_data.append({
                                "channel": channel,
                                "ratio": ratio,
                            })
                            print(f"  ✓ Item {i}: {channel} - {ratio}%")
                        else:
                            print(f"  ⚠ Item {i}: Channel not found")
                            
                    except Exception as e:
                        print(f"  ⚠ Error extracting item {i}: {e}")
                        continue
            
            print(f"  ✓ Total extracted: {len(channel_data)} channel items")
            return channel_data
            
        except Exception as e:
            print(f"  ✗ Error extracting channel data: {e}")
            import traceback
            traceback.print_exc()
            return channel_data
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 유입 채널 데이터 스크래핑"""
        print("\n[Scraping] Starting place inflow channel scraping...")
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 페이지 로딩 대기
        
        # 스크롤하여 데이터가 보이도록 함
        await page.evaluate("window.scrollTo(0, 800)")
        await asyncio.sleep(2)
        
        # 유입 채널 데이터 추출
        all_channel_data = await self.extract_channel_data(page)
        
        # 데이터를 상위 5행과 하위 5행으로 분리
        top_5_data = all_channel_data[:5] if len(all_channel_data) >= 5 else all_channel_data
        bottom_5_data = all_channel_data[5:10] if len(all_channel_data) >= 10 else all_channel_data[5:]
        
        print(f"\n  Data split: Top 5 rows = {len(top_5_data)}, Bottom 5 rows = {len(bottom_5_data)}")
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "channel_data": top_5_data,  # 상위 5행 (현재 폴더에 저장)
            "keyword_data": bottom_5_data,  # 하위 5행 (keyword 폴더에 저장)
            "page_title": await page.title(),
        }
        
        return result
    
    async def save_results(self, data: dict):
        """결과를 파일로 저장 (상위 5행과 하위 5행을 각각 다른 폴더에 저장)"""
        module_name = self.get_module_name()
        
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
        date_suffix = ""
        if self.start_date and self.end_date:
            start_str = self.start_date.replace("-", "")
            end_str = self.end_date.replace("-", "")
            date_suffix = f"__{start_str}_{end_str}"
        
        target_date = self.start_date if self.start_date else self.end_date
        
        # 1. 상위 5행을 현재 폴더(place_inflow_channel)에 저장
        channel_data = data.get("channel_data", [])
        if channel_data:
            # event_dt 추가
            for row in channel_data:
                if isinstance(row, dict):
                    row["event_dt"] = target_date
            
            output_dir = self.get_output_dir()
            df_channel = pd.DataFrame(channel_data)
            csv_filename = f"{module_name}{date_suffix}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            df_channel.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"\n✓ Channel CSV saved: {csv_path} ({len(channel_data)} rows)")
            
            # JSON도 저장
            json_filename = f"{module_name}{date_suffix}.json"
            json_path = os.path.join(output_dir, json_filename)
            channel_result = {
                "url": data.get("url"),
                "scraped_at": data.get("scraped_at"),
                "channel_data": channel_data,
                "page_title": data.get("page_title"),
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(channel_result, f, ensure_ascii=False, indent=2)
            print(f"✓ Channel JSON saved: {json_path}")
        
        # 2. 하위 5행을 place_inflow_keyword 폴더에 저장 (channel -> keyword로 변경)
        keyword_data = data.get("keyword_data", [])
        if keyword_data:
            # channel 컬럼을 keyword로 변경
            keyword_data_renamed = []
            for row in keyword_data:
                if isinstance(row, dict):
                    new_row = {
                        "keyword": row.get("channel"),  # channel -> keyword
                        "ratio": row.get("ratio"),
                        "event_dt": target_date
                    }
                    keyword_data_renamed.append(new_row)
            
            # place_inflow_keyword 폴더에 저장
            keyword_output_dir = os.path.join(self.output_base_dir, "place_inflow_keyword")
            os.makedirs(keyword_output_dir, exist_ok=True)
            
            df_keyword = pd.DataFrame(keyword_data_renamed)
            keyword_csv_filename = f"place_inflow_keyword{date_suffix}.csv"
            keyword_csv_path = os.path.join(keyword_output_dir, keyword_csv_filename)
            df_keyword.to_csv(keyword_csv_path, index=False, encoding="utf-8-sig")
            print(f"✓ Keyword CSV saved: {keyword_csv_path} ({len(keyword_data_renamed)} rows)")
            
            # JSON도 저장
            keyword_json_filename = f"place_inflow_keyword{date_suffix}.json"
            keyword_json_path = os.path.join(keyword_output_dir, keyword_json_filename)
            keyword_result = {
                "url": data.get("url"),
                "scraped_at": data.get("scraped_at"),
                "keyword_data": keyword_data_renamed,
                "page_title": data.get("page_title"),
            }
            with open(keyword_json_path, "w", encoding="utf-8") as f:
                json.dump(keyword_result, f, ensure_ascii=False, indent=2)
            print(f"✓ Keyword JSON saved: {keyword_json_path}")

