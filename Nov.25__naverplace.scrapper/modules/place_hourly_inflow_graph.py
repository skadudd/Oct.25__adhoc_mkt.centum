#!/usr/bin/env python3
"""
네이버 스마트플레이스 플레이스 통계 그래프 데이터 스크래퍼 모듈
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import Page
from .base_scraper import BaseScraper


class PlaceHourlyInflowGraphScraper(BaseScraper):
    """플레이스 시간별 유입 그래프 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-11-15", end_date: str = "2025-11-15", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성
        self.stats_url = (
            f"https://new.smartplace.naver.com/bizes/place/5921383/statistics"
            f"?bookingBusinessId=603738&endDate={end_date}&menu=place"
            f"&placeTab=inflow&startDate={start_date}&term=daily"
        )
    
    def get_module_name(self) -> str:
        return "place_hourly_inflow_graph"
    
    async def wait_for_chart_load(self, page: Page, timeout: int = 10000) -> bool:
        """차트가 로드될 때까지 대기"""
        print("\n[Chart] Waiting for chart to load...")
        try:
            await page.wait_for_selector(".Statistics_chart__A_V_H", timeout=timeout)
            print("  ✓ Chart container found")
            await page.wait_for_selector(".Statistics_chart__A_V_H canvas", timeout=5000)
            print("  ✓ Canvas element found")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"  ⚠ Chart loading timeout or error: {e}")
            return False
    
    async def extract_chart_data_via_hover(self, page: Page) -> list:
        """그래프에 롤오버하여 시간별 데이터 추출 (예: "0시 27회")"""
        print("\n[Data Extraction] Extracting time-based chart data via hover...")
        
        chart_data = []
        
        try:
            chart_container = await page.query_selector(".Statistics_chart__A_V_H")
            if not chart_container:
                print("  ✗ Chart container not found")
                return chart_data
            
            canvas = await chart_container.query_selector("canvas")
            if not canvas:
                print("  ✗ Canvas element not found")
                return chart_data
            
            canvas_box = await canvas.bounding_box()
            if not canvas_box:
                print("  ✗ Canvas bounding box not available")
                return chart_data
            
            print(f"  Canvas size: {canvas_box['width']} x {canvas_box['height']}")
            
            chart_start_y = canvas_box['y'] + 20
            chart_end_y = canvas_box['y'] + canvas_box['height'] - 40
            chart_center_y = (chart_start_y + chart_end_y) / 2
            
            num_hours = 24
            chart_width = canvas_box['width']
            chart_data_start_x = canvas_box['x'] + (chart_width * 0.1)
            chart_data_end_x = canvas_box['x'] + (chart_width * 0.9)
            chart_data_width = chart_data_end_x - chart_data_start_x
            step_x = chart_data_width / (num_hours - 1)
            
            for hour in range(num_hours):
                x = chart_data_start_x + (step_x * hour)
                y_positions = [
                    chart_center_y - 40, chart_center_y - 20, chart_center_y,
                    chart_center_y + 20, chart_center_y + 40,
                ]
                
                point_found = False
                best_tooltip = None
                
                for y in y_positions:
                    try:
                        await page.mouse.move(x, y)
                        await asyncio.sleep(0.6)
                        
                        tooltip_result = await page.evaluate(
                            """
                            () => {
                                const allElements = document.querySelectorAll('*');
                                const tooltips = [];
                                
                                for (let el of allElements) {
                                    const style = window.getComputedStyle(el);
                                    const text = (el.innerText || el.textContent || '').trim();
                                    
                                    const isTimeTooltip = (
                                        text.includes('시') || 
                                        text.includes('회') ||
                                        /\\d+시/.test(text) ||
                                        /\\d+회/.test(text)
                                    );
                                    
                                    if (
                                        (style.position === 'absolute' || style.position === 'fixed') &&
                                        style.zIndex > 1000 &&
                                        text &&
                                        text !== '도움말' &&
                                        text.length < 200 &&
                                        !text.includes('조회 기간에 수집된 데이터가 없습니다') &&
                                        !text.includes('시간별') &&
                                        !text.includes('요일별') &&
                                        isTimeTooltip
                                    ) {
                                        const rect = el.getBoundingClientRect();
                                        if (rect.width > 0 && rect.height > 0 && rect.height < 100) {
                                            tooltips.push({
                                                text: text,
                                                x: rect.x,
                                                y: rect.y,
                                                width: rect.width,
                                                height: rect.height,
                                                zIndex: parseInt(style.zIndex) || 0
                                            });
                                        }
                                    }
                                }
                                
                                if (tooltips.length > 0) {
                                    tooltips.sort((a, b) => {
                                        if (b.zIndex !== a.zIndex) return b.zIndex - a.zIndex;
                                        return a.y - b.y;
                                    });
                                    return tooltips[0].text;
                                }
                                
                                return null;
                            }
                            """
                        )
                        
                        if tooltip_result and tooltip_result != "도움말":
                            time_match = re.search(r'(\d+)시', tooltip_result)
                            count_match = re.search(r'(\d+)회', tooltip_result)
                            
                            if time_match or count_match:
                                best_tooltip = {
                                    "text": tooltip_result,
                                    "hour": int(time_match.group(1)) if time_match else hour,
                                    "count": int(count_match.group(1)) if count_match else None,
                                    "y_position": y,
                                }
                                point_found = True
                                break
                                
                    except Exception:
                        continue
                
                if best_tooltip:
                    point_data = {
                        "hour": best_tooltip["hour"],
                        "count": best_tooltip["count"],
                        "tooltip_text": best_tooltip["text"],
                        "x_coordinate": x,
                        "y_coordinate": best_tooltip["y_position"],
                    }
                    chart_data.append(point_data)
                    print(f"  ✓ {best_tooltip['hour']}시: {best_tooltip['text']}")
                else:
                    point_data = {
                        "hour": hour,
                        "count": None,
                        "tooltip_text": None,
                        "x_coordinate": x,
                        "y_coordinate": chart_center_y,
                    }
                    chart_data.append(point_data)
                    if hour % 6 == 0:
                        print(f"  ⚠ {hour}시: No data found")
            
            chart_data.sort(key=lambda x: x["hour"])
            print(f"  ✓ Extracted data from {len([d for d in chart_data if d.get('count') is not None])} time points")
            return chart_data
            
        except Exception as e:
            print(f"  ✗ Error extracting chart data: {e}")
            import traceback
            traceback.print_exc()
            return chart_data
    
    async def extract_chart_data_via_js(self, page: Page) -> dict:
        """JavaScript를 사용하여 차트 데이터 직접 추출"""
        print("\n[Data Extraction] Extracting chart data via JavaScript...")
        
        try:
            chart_data_result = await page.evaluate(
                """
                () => {
                    const canvas = document.querySelector('.Statistics_chart__A_V_H canvas');
                    if (!canvas) return { error: 'Canvas not found' };
                    
                    const result = {
                        source: null,
                        data: null,
                        labels: null,
                        datasets: null,
                        error: null
                    };
                    
                    // Chart.js
                    if (window.Chart && window.Chart.instances) {
                        const charts = window.Chart.instances;
                        const chartIds = Object.keys(charts);
                        if (chartIds.length > 0) {
                            const chart = charts[chartIds[0]];
                            if (chart.data && chart.data.labels && chart.data.datasets) {
                                result.source = 'Chart.js (window.Chart.instances)';
                                result.labels = chart.data.labels;
                                result.datasets = chart.data.datasets.map(ds => ({
                                    label: ds.label,
                                    data: ds.data,
                                    backgroundColor: ds.backgroundColor
                                }));
                                return result;
                            }
                        }
                    }
                    
                    // Vue.js
                    const vueKey = Object.keys(canvas).find(key => key.startsWith('__vue'));
                    if (vueKey) {
                        const vue = canvas[vueKey];
                        if (vue && vue.config && vue.config.data) {
                            const chartMap = vue.config.data;
                            if (chartMap.labels && chartMap.datasets) {
                                result.source = 'Vue.js (__vue__.config.data)';
                                result.labels = chartMap.labels;
                                result.datasets = chartMap.datasets.map(ds => ({
                                    label: ds.label,
                                    data: ds.data,
                                    backgroundColor: ds.backgroundColor
                                }));
                                return result;
                            }
                        }
                    }
                    
                    // Angular
                    const ngKey = Object.keys(canvas).find(key => key.startsWith('__ngContext'));
                    if (ngKey) {
                        const ngContext = canvas[ngKey];
                        if (ngContext && Array.isArray(ngContext)) {
                            const chartMaps = ngContext.filter(item => 
                                item && item.config && item.basicData
                            );
                            if (chartMaps.length > 0) {
                                const chartMap = chartMaps[0].basicData;
                                if (chartMap.labels && chartMap.datasets) {
                                    result.source = 'Angular (__ngContext__)';
                                    result.labels = chartMap.labels;
                                    result.datasets = chartMap.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data,
                                        backgroundColor: ds.backgroundColor
                                    }));
                                    return result;
                                }
                            }
                        }
                    }
                    
                    // ECharts
                    const ecKey = Object.keys(canvas).find(key => key === '__ec__');
                    if (ecKey) {
                        const ecInstance = canvas[ecKey];
                        if (ecInstance && ecInstance.getOption) {
                            const option = ecInstance.getOption();
                            if (option && option.xAxis && option.series) {
                                result.source = 'ECharts (__ec__)';
                                result.labels = option.xAxis[0]?.data || [];
                                result.datasets = option.series.map(s => ({
                                    label: s.name,
                                    data: s.data,
                                    type: s.type
                                }));
                                return result;
                            }
                        }
                    }
                    
                    // React Fiber
                    const reactKey = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                    if (reactKey) {
                        let fiber = canvas[reactKey];
                        for (let i = 0; i < 100 && fiber; i++) {
                            if (fiber.memoizedProps) {
                                const props = fiber.memoizedProps;
                                
                                if (props.data && props.data.labels && props.data.datasets) {
                                    result.source = 'React (Chart.js props)';
                                    result.labels = props.data.labels;
                                    result.datasets = props.data.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                                
                                if (props.data && Array.isArray(props.data)) {
                                    result.source = 'React (props.data array)';
                                    result.data = props.data;
                                    return result;
                                }
                                
                                if (props.dataset && Array.isArray(props.dataset)) {
                                    result.source = 'React (props.dataset)';
                                    result.datasets = props.dataset;
                                    return result;
                                }
                                
                                if (props.options && props.options.data) {
                                    result.source = 'React (props.options.data)';
                                    result.data = props.options.data;
                                    return result;
                                }
                            }
                            
                            if (fiber.memoizedState) {
                                let state = fiber.memoizedState;
                                while (state) {
                                    if (state.memoizedState) {
                                        const stateData = state.memoizedState;
                                        if (stateData.data && Array.isArray(stateData.data)) {
                                            result.source = 'React (memoizedState)';
                                            result.data = stateData.data;
                                            return result;
                                        }
                                        if (stateData.labels && stateData.datasets) {
                                            result.source = 'React (memoizedState chart)';
                                            result.labels = stateData.labels;
                                            result.datasets = stateData.datasets;
                                            return result;
                                        }
                                    }
                                    state = state.next;
                                }
                            }
                            
                            fiber = fiber.return;
                        }
                    }
                    
                    // 차트 컨테이너에서 Vue/Angular 찾기
                    const chartContainer = document.querySelector('.Statistics_chart__A_V_H');
                    if (chartContainer) {
                        const containerVueKey = Object.keys(chartContainer).find(key => 
                            key.startsWith('__vue')
                        );
                        if (containerVueKey && chartContainer[containerVueKey]) {
                            const vue = chartContainer[containerVueKey];
                            if (vue.$data && vue.$data.chartData) {
                                result.source = 'Vue (container $data)';
                                result.data = vue.$data.chartData;
                                return result;
                            }
                        }
                        
                        const containerNgKey = Object.keys(chartContainer).find(key => 
                            key.startsWith('__ngContext')
                        );
                        if (containerNgKey && chartContainer[containerNgKey]) {
                            const ngContext = chartContainer[containerNgKey];
                            if (Array.isArray(ngContext)) {
                                for (let item of ngContext) {
                                    if (item && item.chartData) {
                                        result.source = 'Angular (container context)';
                                        result.data = item.chartData;
                                        return result;
                                    }
                                }
                            }
                        }
                    }
                    
                    result.error = 'No chart data found in any known structure';
                    return result;
                }
                """
            )
            
            parsed_result = await page.evaluate(
                """
                (chartDataResult) => {
                    if (!chartDataResult || chartDataResult.error) {
                        return {
                            parsed_data: [],
                            time_based_data: []
                        };
                    }
                    
                    const parsed_data = [];
                    const time_based_data = [];
                    
                    const labels = chartDataResult.labels || [];
                    const datasets = chartDataResult.datasets || [];
                    
                    if (labels.length > 0 && datasets.length > 0) {
                        const main_dataset = datasets[0];
                        if (main_dataset && main_dataset.data) {
                            for (let i = 0; i < labels.length && i < main_dataset.data.length; i++) {
                                parsed_data.push({
                                    label: labels[i],
                                    value: main_dataset.data[i],
                                    hour: i
                                });
                            }
                        }
                    } else if (chartDataResult.data && Array.isArray(chartDataResult.data)) {
                        const dataArray = chartDataResult.data;
                        for (let i = 0; i < dataArray.length; i++) {
                            parsed_data.push({
                                hour: i,
                                value: dataArray[i]
                            });
                        }
                    }
                    
                    for (let item of parsed_data) {
                        const hour = item.hour !== undefined ? item.hour : 
                                    (item.label ? parseInt(item.label.replace(/[^0-9]/g, '')) : null);
                        const count = item.value !== undefined ? item.value : null;
                        
                        if (hour !== null && hour !== undefined) {
                            time_based_data.push({
                                hour: hour,
                                count: count,
                                label: item.label || (hour + '시'),
                                tooltip_text: count !== null ? (hour + '시 ' + count + '회') : (hour + '시')
                            });
                        }
                    }
                    
                    return {
                        parsed_data: parsed_data,
                        time_based_data: time_based_data
                    };
                }
                """,
                chart_data_result
            )
            
            result = {
                "chart_library": chart_data_result.get('source') if chart_data_result else None,
                "raw_data": chart_data_result,
                "parsed_data": parsed_result.get('parsed_data', []) if parsed_result else [],
                "time_based_data": parsed_result.get('time_based_data', []) if parsed_result else [],
                "error": chart_data_result.get('error') if chart_data_result else None,
            }
            
            if chart_data_result and not chart_data_result.get('error'):
                print(f"  ✓ Chart library: {chart_data_result.get('source')}")
                time_based_data = result.get("time_based_data", [])
                if time_based_data:
                    print(f"  ✓ Parsed {len(time_based_data)} time-based data points")
                    for i, item in enumerate(time_based_data[:3]):
                        if item.get('count') is not None:
                            print(f"    - {item.get('hour')}시: {item.get('count')}회")
            else:
                error_msg = chart_data_result.get('error') if chart_data_result else 'No data found'
                print(f"  ⚠ {error_msg}")
            
            return result
            
        except Exception as e:
            print(f"  ✗ Error extracting via JS: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    async def setup_network_interception(self, page: Page):
        """네트워크 요청을 가로채서 데이터 추출"""
        print("\n[Network] Setting up network interception...")
        
        async def handle_response(response):
            url = response.url
            if any(keyword in url.lower() for keyword in ['statistics', 'chart', 'data', 'api']):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = await response.json()
                        self.network_responses.append({
                            "url": url,
                            "status": response.status,
                            "data": data,
                        })
                        print(f"  ✓ Captured API response: {url[:80]}...")
                except Exception:
                    pass
        
        page.on("response", handle_response)
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 데이터 스크래핑"""
        print("\n[Scraping] Starting place statistics scraping...")
        
        await self.setup_network_interception(page)
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        
        if not await self.wait_for_chart_load(page):
            print("  ⚠ Chart may not be fully loaded, continuing anyway...")
        
        await asyncio.sleep(3)
        
        js_data = await self.extract_chart_data_via_js(page)
        
        if not js_data.get("time_based_data") or len(js_data.get("time_based_data", [])) == 0:
            print("\n  ⚠ JS extraction found no data, trying hover method...")
            hover_data = await self.extract_chart_data_via_hover(page)
        else:
            hover_data = js_data.get("time_based_data", [])
            print(f"\n  ✓ Using data from JS extraction ({len(hover_data)} points)")
        
        api_data = []
        for resp in self.network_responses:
            if resp.get("data"):
                api_data.append({
                    "url": resp["url"],
                    "status": resp["status"],
                    "has_data": True,
                })
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "hover_data": hover_data,
            "js_data": js_data,
            "network_responses": api_data,
            "page_title": await page.title(),
        }
        
        if js_data.get("raw_data"):
            result["chart_raw_data"] = js_data["raw_data"]
        
        if self.network_responses:
            result["network_data_details"] = self.network_responses[:5]
        
        return result

