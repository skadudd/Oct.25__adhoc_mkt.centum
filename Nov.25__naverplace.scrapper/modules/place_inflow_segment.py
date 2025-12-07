#!/usr/bin/env python3
"""
네이버 스마트플레이스 플레이스 유입 성별·연령 데이터 스크래퍼 모듈
"""

import asyncio
from datetime import datetime
from playwright.async_api import Page
from .base_scraper import BaseScraper


class PlaceInflowSegmentScraper(BaseScraper):
    """플레이스 유입 성별·연령 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-11-15", end_date: str = "2025-11-15", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성 (place_hourly_inflow_graph와 동일한 페이지)
        self.stats_url = (
            f"https://new.smartplace.naver.com/bizes/place/5921383/statistics"
            f"?bookingBusinessId=603738&endDate={end_date}&menu=place"
            f"&placeTab=inflow&startDate={start_date}&term=daily"
        )
    
    def get_module_name(self) -> str:
        return "place_inflow_segment"
    
    async def extract_segment_data(self, page: Page) -> list:
        """성별·연령 데이터 추출"""
        print("\n[Data Extraction] Extracting gender and age segment data...")
        
        segment_data = []
        
        try:
            # JavaScript로 직접 데이터 추출 (실제 HTML 구조에 맞춤)
            js_result = await page.evaluate(
                """
                () => {
                    const result = {
                        gender_data: [],
                        age_data: [],
                        debug: {
                            container_found: false,
                            age_area_found: false,
                            age_items_count: 0
                        }
                    };
                    
                    // 연령대별 데이터 수집 (직접 Statistics_bargraph_area__BEo44 찾기)
                    const ageArea = document.querySelector('.Statistics_bargraph_area__BEo44');
                    if (ageArea) {
                        result.debug.age_area_found = true;
                        
                        // 직접 자식 div들 찾기 (각 연령대 항목)
                        const ageItems = Array.from(ageArea.children).filter(child => child.tagName === 'DIV');
                        result.debug.age_items_count = ageItems.length;
                        
                        for (let item of ageItems) {
                            // 연령 추출
                            const ageEl = item.querySelector('.Statistics_age__HHOgN');
                            const age = ageEl ? (ageEl.innerText || ageEl.textContent).trim() : null;
                            
                            if (!age) continue;
                            
                            // 남성/여성 비율 추출
                            // strong 태그들 찾기
                            const strongEls = item.querySelectorAll('strong.Statistics_percent__5Tb06');
                            let maleRatio = null;
                            let femaleRatio = null;
                            
                            for (let strongEl of strongEls) {
                                // 텍스트 추출 (<em>%</em> 제거)
                                let text = '';
                                for (let node of strongEl.childNodes) {
                                    if (node.nodeType === 3) { // 텍스트 노드
                                        text += node.textContent;
                                    } else if (node.nodeType === 1 && node.tagName !== 'EM') { // 요소 노드 (em 제외)
                                        text += node.textContent;
                                    }
                                }
                                
                                if (!text) {
                                    text = strongEl.innerText || strongEl.textContent;
                                }
                                
                                const ratioValue = text.replace('%', '').replace('％', '').trim();
                                
                                // 여성 클래스 확인
                                if (strongEl.classList.contains('Statistics_woman__xHyvR')) {
                                    femaleRatio = ratioValue;
                                } else {
                                    // 남성 비율 (여성 클래스가 없는 첫 번째)
                                    if (maleRatio === null) {
                                        maleRatio = ratioValue;
                                    }
                                }
                            }
                            
                            // 남성 데이터 추가
                            if (maleRatio !== null) {
                                result.age_data.push({
                                    gender: '남성',
                                    age: age,
                                    ratio: maleRatio
                                });
                            }
                            
                            // 여성 데이터 추가
                            if (femaleRatio !== null) {
                                result.age_data.push({
                                    gender: '여성',
                                    age: age,
                                    ratio: femaleRatio
                                });
                            }
                        }
                    }
                    
                    // 성별 데이터 수집 (전체 성별 비율)
                    // Statistics_bargraph_area__BEo44 외부의 Statistics_percent__5Tb06 div들을 찾기
                    const allPercentDivs = document.querySelectorAll('div.Statistics_percent__5Tb06');
                    const genderDivs = [];
                    
                    for (let div of allPercentDivs) {
                        // Statistics_bargraph_area__BEo44 안에 있지 않은 것만 (성별 전체 데이터)
                        if (!div.closest('.Statistics_bargraph_area__BEo44')) {
                            // strong 태그가 아닌 div만 (연령대별은 strong 태그 사용)
                            if (div.tagName === 'DIV') {
                                genderDivs.push(div);
                            }
                        }
                    }
                    
                    // 첫 번째 div는 남성, 두 번째 div는 여성
                    if (genderDivs.length >= 1) {
                        // 남성 비율 추출
                        let maleText = '';
                        for (let node of genderDivs[0].childNodes) {
                            if (node.nodeType === 3) { // 텍스트 노드
                                maleText += node.textContent;
                            } else if (node.nodeType === 1 && node.tagName !== 'EM') { // 요소 노드 (em 제외)
                                maleText += node.textContent;
                            }
                        }
                        if (!maleText) {
                            maleText = genderDivs[0].innerText || genderDivs[0].textContent;
                        }
                        const maleRatio = maleText.replace('%', '').replace('％', '').trim();
                        if (maleRatio) {
                            result.gender_data.push({
                                gender: '남성',
                                ratio: maleRatio
                            });
                        }
                    }
                    
                    if (genderDivs.length >= 2) {
                        // 여성 비율 추출
                        let femaleText = '';
                        for (let node of genderDivs[1].childNodes) {
                            if (node.nodeType === 3) { // 텍스트 노드
                                femaleText += node.textContent;
                            } else if (node.nodeType === 1 && node.tagName !== 'EM') { // 요소 노드 (em 제외)
                                femaleText += node.textContent;
                            }
                        }
                        if (!femaleText) {
                            femaleText = genderDivs[1].innerText || genderDivs[1].textContent;
                        }
                        const femaleRatio = femaleText.replace('%', '').replace('％', '').trim();
                        if (femaleRatio) {
                            result.gender_data.push({
                                gender: '여성',
                                ratio: femaleRatio
                            });
                        }
                    }
                    
                    return result;
                }
                """
            )
            
            # 디버깅 정보 출력
            debug_info = js_result.get('debug', {})
            print(f"  Debug: age_area_found={debug_info.get('age_area_found', False)}, age_items_count={debug_info.get('age_items_count', 0)}")
            
            # 성별 전체 비율 저장 (left join을 위해)
            gender_ratios = {}
            if js_result.get('gender_data'):
                for item in js_result['gender_data']:
                    gender = item.get('gender')
                    ratio_str = item.get('ratio', '0')
                    try:
                        # 정수인 경우 0.01을 곱함
                        ratio_value = float(ratio_str)
                        if ratio_value >= 1:  # 정수로 보이는 경우 (예: 37)
                            ratio_value = ratio_value * 0.01
                        gender_ratios[gender] = ratio_value
                    except (ValueError, TypeError):
                        gender_ratios[gender] = 0.0
                print(f"  ✓ Extracted {len(js_result['gender_data'])} gender items")
                for gender, ratio in gender_ratios.items():
                    print(f"    - {gender}: {ratio:.4f} ({ratio*100:.2f}%)")
            
            # 연령대별 데이터 처리 (성별 전체 비율과 곱하기)
            if js_result.get('age_data'):
                for item in js_result['age_data']:
                    gender = item.get('gender')
                    age = item.get('age')
                    ratio_str = item.get('ratio', '0')
                    
                    try:
                        # 나이대별 비율을 숫자로 변환
                        age_ratio = float(ratio_str)
                        if age_ratio >= 1:  # 정수로 보이는 경우 (예: 3)
                            age_ratio = age_ratio * 0.01
                        
                        # 성별 전체 비율 가져오기 (left join)
                        gender_total_ratio = gender_ratios.get(gender, 1.0)  # 없으면 1.0 사용
                        
                        # 최종 비율 계산 (성별 전체 비율 * 나이대별 비율)
                        final_ratio = gender_total_ratio * age_ratio
                        
                        segment_data.append({
                            "gender": gender,
                            "age": age,
                            "ratio": final_ratio,
                        })
                    except (ValueError, TypeError):
                        # 변환 실패 시 원본 값 사용
                        segment_data.append({
                            "gender": gender,
                            "age": age,
                            "ratio": ratio_str,
                        })
                print(f"  ✓ Extracted {len(js_result['age_data'])} age items (with gender ratio multiplication)")
            
            # 결과 출력
            if segment_data:
                print(f"  ✓ Total extracted: {len(segment_data)} segment items")
                for i, item in enumerate(segment_data[:10], 1):
                    age_str = item.get('age') if item.get('age') else '전체'
                    ratio_value = item.get('ratio')
                    if isinstance(ratio_value, (int, float)):
                        print(f"    {i}. {item.get('gender')} - {age_str} - {ratio_value:.4f} ({ratio_value*100:.2f}%)")
                    else:
                        print(f"    {i}. {item.get('gender')} - {age_str} - {ratio_value}")
            else:
                print("  ⚠ No data extracted")
                
                # Playwright 방식으로 재시도
                print("  Trying Playwright selectors...")
                container = await page.query_selector(".SectionBox_root__SjdXC")
                if container:
                    print("  ✓ Container found")
                    
                    # 성별 전체 비율 저장
                    gender_ratios_fallback = {}
                    
                    # 성별 데이터 수집
                    all_percent_divs = await container.query_selector_all("div.Statistics_percent__5Tb06")
                    gender_divs = []
                    for div in all_percent_divs:
                        is_in_age_area = await div.evaluate("el => el.closest('.Statistics_bargraph_area__BEo44') !== null")
                        if not is_in_age_area:
                            gender_divs.append(div)
                    
                    # 첫 번째 div = 남성, 두 번째 div = 여성
                    if len(gender_divs) >= 1:
                        male_text = await gender_divs[0].inner_text()
                        male_ratio_str = male_text.replace("%", "").replace("％", "").strip()
                        try:
                            male_ratio_value = float(male_ratio_str)
                            if male_ratio_value >= 1:
                                male_ratio_value = male_ratio_value * 0.01
                            gender_ratios_fallback["남성"] = male_ratio_value
                        except (ValueError, TypeError):
                            gender_ratios_fallback["남성"] = 0.0
                    
                    if len(gender_divs) >= 2:
                        female_text = await gender_divs[1].inner_text()
                        female_ratio_str = female_text.replace("%", "").replace("％", "").strip()
                        try:
                            female_ratio_value = float(female_ratio_str)
                            if female_ratio_value >= 1:
                                female_ratio_value = female_ratio_value * 0.01
                            gender_ratios_fallback["여성"] = female_ratio_value
                        except (ValueError, TypeError):
                            gender_ratios_fallback["여성"] = 0.0
                    
                    # 연령대별 데이터
                    age_area = await container.query_selector(".Statistics_bargraph_area__BEo44")
                    if age_area:
                        # 직접 자식 div들 찾기 (JavaScript로)
                        age_items_data = await age_area.evaluate("""
                            () => {
                                const items = Array.from(this.children).filter(child => child.tagName === 'DIV');
                                return items.map((item, index) => {
                                    const ageEl = item.querySelector('.Statistics_age__HHOgN');
                                    const age = ageEl ? (ageEl.innerText || ageEl.textContent).trim() : null;
                                    
                                    const strongEls = item.querySelectorAll('strong.Statistics_percent__5Tb06');
                                    let maleRatio = null;
                                    let femaleRatio = null;
                                    
                                    for (let strongEl of strongEls) {
                                        let text = '';
                                        for (let node of strongEl.childNodes) {
                                            if (node.nodeType === 3) {
                                                text += node.textContent;
                                            } else if (node.nodeType === 1 && node.tagName !== 'EM') {
                                                text += node.textContent;
                                            }
                                        }
                                        if (!text) {
                                            text = strongEl.innerText || strongEl.textContent;
                                        }
                                        
                                        const ratioStr = text.replace('%', '').replace('％', '').trim();
                                        try {
                                            let ratioValue = parseFloat(ratioStr);
                                            if (ratioValue >= 1) {
                                                ratioValue = ratioValue * 0.01;
                                            }
                                            
                                            if (strongEl.classList.contains('Statistics_woman__xHyvR')) {
                                                femaleRatio = ratioValue;
                                            } else {
                                                if (maleRatio === null) {
                                                    maleRatio = ratioValue;
                                                }
                                            }
                                        } catch (e) {}
                                    }
                                    
                                    return { age, maleRatio, femaleRatio };
                                });
                            }
                        """)
                        
                        for item_data in age_items_data:
                            age = item_data.get('age')
                            if age:
                                male_ratio = item_data.get('maleRatio')
                                female_ratio = item_data.get('femaleRatio')
                                
                                # 남성 데이터 추가 (성별 전체 비율과 곱하기)
                                if male_ratio is not None:
                                    gender_total = gender_ratios_fallback.get("남성", 1.0)
                                    final_male_ratio = gender_total * male_ratio
                                    segment_data.append({
                                        "gender": "남성",
                                        "age": age,
                                        "ratio": final_male_ratio,
                                    })
                                
                                # 여성 데이터 추가 (성별 전체 비율과 곱하기)
                                if female_ratio is not None:
                                    gender_total = gender_ratios_fallback.get("여성", 1.0)
                                    final_female_ratio = gender_total * female_ratio
                                    segment_data.append({
                                        "gender": "여성",
                                        "age": age,
                                        "ratio": final_female_ratio,
                                    })
            
            print(f"  ✓ Final total: {len(segment_data)} segment items")
            return segment_data
            
        except Exception as e:
            print(f"  ✗ Error extracting segment data: {e}")
            import traceback
            traceback.print_exc()
            return segment_data
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 성별·연령 데이터 스크래핑"""
        print("\n[Scraping] Starting place inflow segment scraping...")
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 페이지 로딩 대기
        
        # 스크롤하여 데이터가 보이도록 함
        await page.evaluate("window.scrollTo(0, 1000)")
        await asyncio.sleep(2)
        
        # 성별·연령 데이터 추출
        segment_data = await self.extract_segment_data(page)
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "segment_data": segment_data,
            "page_title": await page.title(),
        }
        
        return result

