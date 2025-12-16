#!/usr/bin/env python3
"""
네이버 스마트플레이스 데이터 수집 메인 실행 파일

구조:
- 로그인 후 각 모듈을 실행하여 데이터 각기 수집 후 각 폴더에 저장
- 세션 종료
"""

import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from modules.naverplace_login import NaverPlaceLogin, load_credentials
from modules import PlaceHourlyInflowGraphScraper, PlaceInflowChannelScraper, PlaceInflowSegmentScraper, SmartcallCallStatisticsScraper, SmartcallTopMediaScraper, SmartcallTopKeywordScraper


class NaverPlaceDataCollector:
    """네이버 스마트플레이스 데이터 수집기"""
    
    def __init__(self, username: str, password: str, output_base_dir: str = "data/naverplace"):
        self.username = username
        self.password = password
        self.output_base_dir = output_base_dir
        self.login_handler = NaverPlaceLogin(username, password)
        self.scrapers = []  # 스크래퍼 템플릿 리스트
    
    def register_scraper(self, scraper):
        """스크래퍼 등록 (템플릿으로 사용)"""
        self.scrapers.append(scraper)
    
    async def run(self) -> bool:
        """메인 실행 함수"""
        print("=" * 70)
        print("Naver SmartPlace Data Collector")
        print("=" * 70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Step 1: 로그인
                print("\n[Step 1] Logging in...")
                if not await self.login_handler.perform_login(page):
                    print("  ✗ Login failed")
                    return False
                
                # 베이스 페이지로 이동
                if not await self.login_handler.navigate_to_base(page):
                    print("  ⚠ Navigation warning, continuing...")
                
                # Step 2: 각 모듈 실행하여 데이터 수집
                print("\n[Step 2] Running scrapers...")
                results = {}
                
                for i, scraper_template in enumerate(self.scrapers, 1):
                    module_name = scraper_template.get_module_name()
                    start_date = scraper_template.start_date
                    end_date = scraper_template.end_date
                    
                    # 날짜 범위 파싱
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    except ValueError as e:
                        print(f"\n✗ Invalid date format in {module_name}: {e}")
                        results[module_name] = f"✗ Error: Invalid date format"
                        continue
                    
                    # 날짜 범위 생성
                    current_date = start_dt
                    date_list = []
                    while current_date <= end_dt:
                        date_list.append(current_date.strftime("%Y-%m-%d"))
                        current_date += timedelta(days=1)
                    
                    print(f"\n{'=' * 70}")
                    print(f"Scraper {i}/{len(self.scrapers)}: {module_name}")
                    print(f"Date range: {start_date} to {end_date} ({len(date_list)} days)")
                    print("=" * 70)
                    
                    # 각 날짜별로 데이터 수집
                    date_results = {}
                    for date_idx, target_date in enumerate(date_list, 1):
                        print(f"\n[{date_idx}/{len(date_list)}] Processing date: {target_date}")
                        
                        try:
                            # 각 날짜별로 새로운 스크래퍼 인스턴스 생성 (start_date=end_date=target_date)
                            scraper_class = type(scraper_template)
                            
                            # 스크래퍼 클래스에 따라 적절한 인스턴스 생성
                            if scraper_class == PlaceHourlyInflowGraphScraper:
                                scraper = PlaceHourlyInflowGraphScraper(
                                    self.username,
                                    self.password,
                                    start_date=target_date,
                                    end_date=target_date,
                                    output_base_dir=self.output_base_dir
                                )
                            elif scraper_class == PlaceInflowChannelScraper:
                                scraper = PlaceInflowChannelScraper(
                                    self.username,
                                    self.password,
                                    start_date=target_date,
                                    end_date=target_date,
                                    output_base_dir=self.output_base_dir
                                )
                            elif scraper_class == PlaceInflowSegmentScraper:
                                scraper = PlaceInflowSegmentScraper(
                                    self.username,
                                    self.password,
                                    start_date=target_date,
                                    end_date=target_date,
                                    output_base_dir=self.output_base_dir
                                )
                            else:
                                # 일반적인 방법으로 생성
                                scraper = scraper_class(
                                    self.username,
                                    self.password,
                                    start_date=target_date,
                                    end_date=target_date,
                                    output_base_dir=self.output_base_dir
                                )
                            
                            # 데이터 수집
                            data = await scraper.scrape(page)
                            await scraper.save_results(data)
                            date_results[target_date] = "✓ Success"
                            print(f"  ✓ {target_date} completed successfully")
                            
                        except Exception as e:
                            print(f"  ✗ Error on {target_date}: {e}")
                            import traceback
                            traceback.print_exc()
                            date_results[target_date] = f"✗ Error: {str(e)}"
                        
                        # 날짜 간 대기 시간
                        if date_idx < len(date_list):
                            await asyncio.sleep(1)
                    
                    # 날짜별 결과 요약
                    success_count = sum(1 for status in date_results.values() if status.startswith("✓"))
                    if success_count == len(date_list):
                        results[module_name] = f"✓ Success ({success_count}/{len(date_list)} dates)"
                    else:
                        results[module_name] = f"⚠ Partial ({success_count}/{len(date_list)} dates)"
                    
                    # 모듈 간 대기 시간
                    if i < len(self.scrapers):
                        await asyncio.sleep(2)
                
                # Step 3: 결과 요약
                print("\n" + "=" * 70)
                print("SUMMARY")
                print("=" * 70)
                for module_name, status in results.items():
                    print(f"  {module_name}: {status}")
                print("=" * 70)
                
                return True
                
            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()
                return False
                
            finally:
                # Step 4: 세션 종료
                print("\n[Step 3] Closing browser session...")
                await browser.close()
                print("✓ Browser session closed")


def main():
    """메인 함수"""
    # 자격증명 로드
    username, password = load_credentials()
    
    # 날짜 설정 (기본값 또는 사용자 지정)
    start_date = "2025-11-15"
    end_date = "2025-11-18"
    
    # 데이터 수집기 생성
    collector = NaverPlaceDataCollector(username, password)
    
    # # 스크래퍼 등록 (start_date, end_date 파라미터 포함)
    # collector.register_scraper(
    #     PlaceHourlyInflowGraphScraper(
    #         username, 
    #         password,
    #         start_date=start_date,
    #         end_date=end_date
    #     )
    # )

    # collector.register_scraper(
    #     PlaceInflowChannelScraper(
    #         username, 
    #         password,
    #         start_date=start_date,
    #         end_date=end_date
    #     )
    # )

    # collector.register_scraper(
    #     PlaceInflowSegmentScraper(
    #         username, 
    #         password,
    #         start_date=start_date,
    #         end_date=end_date
    #     )
    # )

    collector.register_scraper(
        SmartcallCallStatisticsScraper(
            username, password,
            start_date="2025-12-13",
            end_date="2025-12-15"
        )
    )

    # collector.register_scraper(
    #     SmartcallTopMediaScraper(
    #         username, password,
    #         start_date="2025-12-09",
    #         end_date="2025-12-15"
    #     )
    # )

    # collector.register_scraper(
    #     SmartcallTopKeywordScraper(
    #         username, password,
    #         start_date="2025-12-09",
    #         end_date="2025-12-15"
    #     )
    # )    

    asyncio.run(collector.run())

if __name__ == "__main__":
    main()

