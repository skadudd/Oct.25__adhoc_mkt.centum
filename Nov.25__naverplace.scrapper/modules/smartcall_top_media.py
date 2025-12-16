#!/usr/bin/env python3
"""
네이버 스마트플레이스 스마트콜 전화가 많이 오는 매체 데이터 스크래퍼 모듈
"""

import asyncio
from datetime import datetime
from playwright.async_api import Page
from .base_scraper import BaseScraper


class SmartcallTopMediaScraper(BaseScraper):
    """스마트콜 전화가 많이 오는 매체 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-12-09", end_date: str = "2025-12-15", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성
        self.stats_url = (
            f"https://smartcall.smartplace.naver.com/statistics/1191881927"
            f"?startDate={start_date}&endDate={end_date}&bookingBusinessId=603738"
        )
    
    def get_module_name(self) -> str:
        return "smartcall_top_media"
    
    async def extract_top_media_data(self, page: Page) -> list:
        """전화가 많이 오는 매체 데이터 추출"""
        print("\n[Data Extraction] Extracting top media data...")
        
        media_data = []
        
        try:
            # 섹션 찾기
            section_selector = "#__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3)"
            
            await page.wait_for_selector(section_selector, timeout=10000)
            await asyncio.sleep(2)
            
            # JavaScript로 데이터 추출 (task.md에 명시된 selector 사용)
            js_result = await page.evaluate(
                """
                () => {
                    const result = {
                        items_found: 0,
                        data: []
                    };
                    
                    // 섹션 찾기
                    const section = document.querySelector('#__next > div > div:nth-child(3) > div > div.call_section > div:nth-child(3)');
                    if (!section) {
                        return result;
                    }
                    
                    // ul > li 찾기 (task.md에 명시된 구조)
                    const ul = section.querySelector('div > ul');
                    if (!ul) {
                        return result;
                    }
                    
                    const items = ul.querySelectorAll('li');
                    result.items_found = items.length;
                    
                    // 각 li에서 3개의 열 수집
                    for (let i = 0; i < items.length; i++) {
                        const li = items[i];
                        
                        // 1. 순위 번호: strong.styles_rank_num__Pkqpj
                        const rankNumEl = li.querySelector('strong.styles_rank_num__Pkqpj');
                        const rankNum = rankNumEl ? (rankNumEl.innerText || rankNumEl.textContent || '').trim() : null;
                        
                        // 2. 매체명: strong.styles_rank_name__usvhI
                        const rankNameEl = li.querySelector('strong.styles_rank_name__usvhI');
                        const media = rankNameEl ? (rankNameEl.innerText || rankNameEl.textContent || '').trim() : null;
                        
                        // 3. 전체 li에서 개수 추출 (다른 span이나 텍스트에서)
                        let count = null;
                        // li 내의 모든 텍스트를 확인하여 숫자 찾기
                        const liText = (li.innerText || li.textContent || '').trim();
                        // 숫자 패턴 찾기 (순위 번호 제외)
                        const textParts = liText.split(/\\s+/);
                        for (let part of textParts) {
                            // 순위 번호가 아닌 숫자 찾기
                            if (part !== rankNum && /^[0-9]+$/.test(part)) {
                                count = parseInt(part);
                                break;
                            }
                        }
                        // 숫자가 없으면 다른 방법 시도
                        if (count === null) {
                            const spans = li.querySelectorAll('span');
                            for (let span of spans) {
                                const spanText = (span.innerText || span.textContent || '').trim();
                                const match = spanText.match(/[0-9]+/);
                                if (match && spanText !== rankNum) {
                                    count = parseInt(match[0]);
                                    break;
                                }
                            }
                        }
                        
                        if (media) {
                            result.data.push({
                                rank: rankNum,
                                media: media,
                                count: count
                            });
                        }
                    }
                    
                    return result;
                }
                """
            )
            
            print(f"  Found {js_result.get('items_found', 0)} items")
            
            if js_result.get('data'):
                media_data = js_result['data']
                print(f"  ✓ Extracted {len(media_data)} media items")
                for i, item in enumerate(media_data[:5], 1):
                    print(f"    {i}. Rank: {item.get('rank')}, Media: {item.get('media')}, Count: {item.get('count')}")
            else:
                print("  ⚠ No data extracted")
            
            return media_data
            
        except Exception as e:
            print(f"  ✗ Error extracting media data: {e}")
            import traceback
            traceback.print_exc()
            return media_data
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 전화가 많이 오는 매체 데이터 스크래핑"""
        print("\n[Scraping] Starting smartcall top media scraping...")
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 페이지 로딩 대기
        
        # 스크롤하여 데이터가 보이도록 함
        await page.evaluate("window.scrollTo(0, 800)")
        await asyncio.sleep(2)
        
        # 매체 데이터 추출
        media_data = await self.extract_top_media_data(page)
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "top_media_data": media_data,
            "page_title": await page.title(),
        }
        
        return result

