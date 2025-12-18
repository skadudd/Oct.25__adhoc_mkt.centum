#!/usr/bin/env python3
"""
네이버 스마트플레이스 예약 주문 예약 트렌드 차트 데이터 스크래퍼 모듈
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import Page
from .base_scraper import BaseScraper


class BookingTrendChartScraper(BaseScraper):
    """예약 트렌드 차트 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-12-15", end_date: str = "2025-12-21", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성 (period=1은 일별, period=2는 주별)
        period = 1  # 일별 데이터
        self.stats_url = (
            f"https://partner.booking.naver.com/bizes/603738/statistics/booking"
            f"?endDate={end_date}&period={period}&startDate={start_date}"
        )
        self.network_responses = []
    
    def get_module_name(self) -> str:
        return "booking_trend_chart"
    
    async def wait_for_chart_load(self, page: Page, timeout: int = 15000) -> bool:
        """차트가 로드될 때까지 대기"""
        print("\n[Chart] Waiting for chart to load...")
        try:
            chart_selector = "#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-body > div > div > div.StatisticsIndicators__chart-wrap__4UCu\\+.StatisticsIndicators__chart-wrap-m__b8qFo"
            await page.wait_for_selector(chart_selector, timeout=timeout)
            print("  ✓ Chart container found")
            await asyncio.sleep(3)  # 차트 렌더링 대기
            return True
        except Exception as e:
            print(f"  ⚠ Chart loading timeout or error: {e}")
            return False
    
    async def get_checkbox_features(self, page: Page) -> list:
        """체크박스 그룹에서 각 피쳐명 추출"""
        print("\n[Checkboxes] Extracting checkbox features...")
        
        features = []
        
        try:
            checkbox_group_selector = "#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div"
            
            await page.wait_for_selector(checkbox_group_selector, timeout=10000)
            await asyncio.sleep(2)
            
            # JavaScript로 체크박스 피쳐명 추출
            js_result = await page.evaluate(
                """
                () => {
                    const result = {
                        features: []
                    };
                    
                    const checkboxGroup = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div');
                    if (!checkboxGroup) {
                        return result;
                    }
                    
                    const labels = checkboxGroup.querySelectorAll('label');
                    for (let label of labels) {
                        const input = label.querySelector('input.check-radio');
                        const span = label.querySelector('span > span');
                        
                        if (input && span) {
                            const featureName = (span.innerText || span.textContent || '').trim();
                            const isChecked = input.checked || false;
                            
                            result.features.push({
                                feature: featureName,
                                checked: isChecked,
                                inputSelector: input.className
                            });
                        }
                    }
                    
                    return result;
                }
                """
            )
            
            if js_result.get('features'):
                features = js_result['features']
                print(f"  ✓ Found {len(features)} checkbox features")
                for i, feat in enumerate(features, 1):
                    status = "✓" if feat.get('checked') else "○"
                    print(f"    {i}. {status} {feat.get('feature')}")
            else:
                print("  ⚠ No checkbox features found")
            
            return features
            
        except Exception as e:
            print(f"  ✗ Error extracting checkbox features: {e}")
            import traceback
            traceback.print_exc()
            return features
    
    async def toggle_checkbox(self, page: Page, checkbox_index: int) -> bool:
        """특정 체크박스를 활성화"""
        try:
            # label을 클릭하는 방식으로 변경 (input이 disabled일 수 있음)
            label_selector = f"#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})"
            
            # label이 나타날 때까지 대기
            await page.wait_for_selector(label_selector, timeout=10000)
            await asyncio.sleep(1)
            
            # JavaScript로 직접 클릭 (더 안정적)
            clicked = await page.evaluate(
                f"""
                () => {{
                    const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                    if (!label) {{
                        return false;
                    }}
                    
                    const input = label.querySelector('input.check-radio');
                    if (!input) {{
                        return false;
                    }}
                    
                    const wasChecked = input.checked;
                    
                    // label 클릭
                    label.click();
                    
                    // 또는 input 직접 클릭 (disabled가 아닌 경우)
                    if (!input.disabled) {{
                        input.click();
                    }}
                    
                    return true;
                }}
                """
            )
            
            if clicked:
                await asyncio.sleep(3)  # 차트 업데이트 대기
                print(f"  ✓ Checkbox {checkbox_index} toggled")
                return True
            else:
                print(f"  ⚠ Failed to toggle checkbox {checkbox_index}")
                return False
                
        except Exception as e:
            print(f"  ⚠ Error toggling checkbox {checkbox_index}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def extract_chart_data_via_hover(self, page: Page) -> list:
        """그래프에 롤오버하여 데이터 추출 (place_hourly_inflow_graph.py 참조)"""
        print("\n[Data Extraction] Extracting chart data via hover...")
        
        chart_data = []
        
        try:
            chart_selector = "#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-body > div > div > div.StatisticsIndicators__chart-wrap__4UCu\\+.StatisticsIndicators__chart-wrap-m__b8qFo"
            
            chart_container = await page.query_selector(chart_selector)
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
            
            # 데이터 포인트 수 추정 (일별이면 날짜 수, 주별이면 주 수)
            num_points = 30  # 기본값
            chart_width = canvas_box['width']
            chart_data_start_x = canvas_box['x'] + (chart_width * 0.1)
            chart_data_end_x = canvas_box['x'] + (chart_width * 0.9)
            chart_data_width = chart_data_end_x - chart_data_start_x
            step_x = chart_data_width / (num_points - 1)
            
            for point_idx in range(num_points):
                x = chart_data_start_x + (step_x * point_idx)
                y_positions = [
                    chart_center_y - 40, chart_center_y - 20, chart_center_y,
                    chart_center_y + 20, chart_center_y + 40,
                ]
                
                point_found = False
                best_tooltip = None
                
                for y in y_positions:
                    try:
                        await page.mouse.move(x, y)
                        await asyncio.sleep(1.0)  # tooltip이 나타날 때까지 충분히 대기
                        
                        tooltip_result = await page.evaluate(
                            """
                            () => {
                                // 1. 모든 div 요소에서 tooltip 찾기
                                const allDivs = document.querySelectorAll('div');
                                const tooltips = [];
                                
                                for (let el of allDivs) {
                                    const style = window.getComputedStyle(el);
                                    const text = (el.innerText || el.textContent || '').trim();
                                    
                                    // tooltip 조건 완화
                                    const hasText = text && text.length > 0 && text.length < 1000;
                                    const isPositioned = style.position === 'absolute' || style.position === 'fixed';
                                    const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
                                    const hasHighZIndex = (parseInt(style.zIndex) || 0) > 50;
                                    const isNotHidden = parseFloat(style.opacity) > 0;
                                    
                                    // 제외할 텍스트
                                    const excludeTexts = [
                                        '도움말', '조회 기간에 수집된 데이터가 없습니다',
                                        'StatisticsIndicators', 'BaseLayout', 'panel-body',
                                        'chart-wrap', '신청', '확정', '취소', '완료', '변경', '노쇼'
                                    ];
                                    const shouldExclude = excludeTexts.some(exclude => text.includes(exclude));
                                    
                                    if (hasText && isPositioned && isVisible && isNotHidden && !shouldExclude) {
                                        const rect = el.getBoundingClientRect();
                                        // 화면에 보이는 요소만
                                        if (rect.width > 0 && rect.height > 0 && 
                                            rect.top >= 0 && rect.left >= 0 &&
                                            rect.top < window.innerHeight &&
                                            rect.left < window.innerWidth &&
                                            rect.height < 200) {  // tooltip은 작은 박스
                                            
                                            // 날짜나 숫자가 포함된 것 우선
                                            const hasDate = /\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}|\d{1,2}일/.test(text);
                                            const hasNumber = /\d/.test(text);
                                            
                                            if (hasDate || hasNumber) {
                                                tooltips.push({
                                                    text: text,
                                                    x: rect.x,
                                                    y: rect.y,
                                                    width: rect.width,
                                                    height: rect.height,
                                                    zIndex: parseInt(style.zIndex) || 0,
                                                    opacity: parseFloat(style.opacity) || 1,
                                                    hasDate: hasDate,
                                                    hasNumber: hasNumber
                                                });
                                            }
                                        }
                                    }
                                }
                                
                                // 2. 모든 요소에서 tooltip 찾기 (fallback)
                                if (tooltips.length === 0) {
                                    const allElements = document.querySelectorAll('*');
                                    for (let el of allElements) {
                                        const style = window.getComputedStyle(el);
                                        const text = (el.innerText || el.textContent || '').trim();
                                        
                                        if (text && text.length > 0 && text.length < 500) {
                                            const rect = el.getBoundingClientRect();
                                            // 마우스 위치 근처의 요소 찾기
                                            const mouseX = window.mouseX || 0;
                                            const mouseY = window.mouseY || 0;
                                            
                                            if (rect.width > 0 && rect.height > 0 &&
                                                Math.abs(rect.x - mouseX) < 200 &&
                                                Math.abs(rect.y - mouseY) < 200) {
                                                
                                                const hasDate = /\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}|\d{1,2}일/.test(text);
                                                const hasNumber = /\d/.test(text);
                                                
                                                if ((hasDate || hasNumber) && 
                                                    (style.position === 'absolute' || style.position === 'fixed') &&
                                                    (parseInt(style.zIndex) || 0) > 100) {
                                                    tooltips.push({
                                                        text: text,
                                                        x: rect.x,
                                                        y: rect.y,
                                                        width: rect.width,
                                                        height: rect.height,
                                                        zIndex: parseInt(style.zIndex) || 0,
                                                        opacity: parseFloat(style.opacity) || 1,
                                                        hasDate: hasDate,
                                                        hasNumber: hasNumber
                                                    });
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                if (tooltips.length > 0) {
                                    // 날짜가 있는 것 우선, 그 다음 숫자가 있는 것
                                    tooltips.sort((a, b) => {
                                        if (a.hasDate !== b.hasDate) return b.hasDate - a.hasDate;
                                        if (a.hasNumber !== b.hasNumber) return b.hasNumber - a.hasNumber;
                                        if (b.zIndex !== a.zIndex) return b.zIndex - a.zIndex;
                                        return a.y - b.y;
                                    });
                                    
                                    return tooltips[0].text;
                                }
                                
                                return null;
                            }
                            """
                        )
                        
                        if tooltip_result and tooltip_result.strip():
                            # tooltip 텍스트에서 날짜와 값 추출
                            # 예: "2025-12-15\n신청: 10" 또는 "12/15\n10" 등
                            best_tooltip = {
                                "text": tooltip_result,
                                "point_index": point_idx,
                                "y_position": y,
                            }
                            point_found = True
                            print(f"    ✓ Found tooltip at point {point_idx}: {tooltip_result[:100]}")
                            break
                        
                        # 디버깅: tooltip이 없는 경우
                        if point_idx == 0 and y == y_positions[0]:
                            # 첫 번째 포인트에서 tooltip이 없는 경우 디버깅 정보 출력
                            debug_info = await page.evaluate(
                                """
                                () => {
                                    const allDivs = document.querySelectorAll('div');
                                    const candidates = [];
                                    
                                    for (let el of allDivs) {
                                        const style = window.getComputedStyle(el);
                                        const text = (el.innerText || el.textContent || '').trim();
                                        
                                        if (text && text.length > 0 && text.length < 200) {
                                            const rect = el.getBoundingClientRect();
                                            if (rect.width > 0 && rect.height > 0) {
                                                candidates.push({
                                                    text: text.substring(0, 50),
                                                    position: style.position,
                                                    zIndex: parseInt(style.zIndex) || 0,
                                                    display: style.display,
                                                    visibility: style.visibility,
                                                    opacity: parseFloat(style.opacity) || 1,
                                                    rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}
                                                });
                                            }
                                        }
                                    }
                                    
                                    return candidates.slice(0, 10);  // 처음 10개만
                                }
                                """
                            )
                            if debug_info:
                                print(f"    [Debug] Found {len(debug_info)} candidate elements")
                                for i, cand in enumerate(debug_info[:3], 1):
                                    print(f"      {i}. {cand.get('text', '')[:30]} (z:{cand.get('zIndex')}, pos:{cand.get('position')})")
                                
                    except Exception:
                        continue
                
                if best_tooltip:
                    # tooltip 텍스트 파싱
                    tooltip_text = best_tooltip["text"]
                    
                    # 날짜와 값 추출 시도
                    # 예: "2025-12-15\n신청: 10" 또는 "12/15\n10" 또는 "15일\n10건"
                    lines = tooltip_text.split('\n')
                    date_label = None
                    value = None
                    feature_name = None
                    
                    for line in lines:
                        line = line.strip()
                        # 날짜 형식 찾기
                        if not date_label and (re.search(r'\d{4}-\d{2}-\d{2}', line) or 
                                               re.search(r'\d{1,2}/\d{1,2}', line) or
                                               re.search(r'\d{1,2}일', line)):
                            date_label = line
                        # 숫자 값 찾기
                        if not value:
                            num_match = re.search(r'(\d+(?:,\d+)*)', line)
                            if num_match:
                                value = int(num_match.group(1).replace(',', ''))
                        # 피쳐명 찾기 (한글)
                        if not feature_name and re.search(r'[가-힣]+', line):
                            feature_match = re.search(r'([가-힣]+)', line)
                            if feature_match and feature_match.group(1) not in ['일', '건', '개']:
                                feature_name = feature_match.group(1)
                    
                    point_data = {
                        "point_index": best_tooltip["point_index"],
                        "tooltip_text": tooltip_text,
                        "label": date_label,
                        "value": value,
                        "feature": feature_name,
                        "x_coordinate": x,
                        "y_coordinate": best_tooltip["y_position"],
                    }
                    chart_data.append(point_data)
                    if point_idx % 5 == 0 or value is not None:
                        print(f"  ✓ Point {point_idx}: {date_label or 'N/A'} - {value or 'N/A'} ({feature_name or 'N/A'})")
                else:
                    point_data = {
                        "point_index": point_idx,
                        "tooltip_text": None,
                        "label": None,
                        "value": None,
                        "feature": None,
                        "x_coordinate": x,
                        "y_coordinate": chart_center_y,
                    }
                    chart_data.append(point_data)
            
            print(f"  ✓ Extracted data from {len([d for d in chart_data if d.get('tooltip_text')])} data points")
            return chart_data
            
        except Exception as e:
            print(f"  ✗ Error extracting chart data: {e}")
            import traceback
            traceback.print_exc()
            return chart_data
    
    async def extract_chart_data_via_js(self, page: Page) -> dict:
        """JavaScript를 사용하여 차트 데이터 직접 추출 (place_hourly_inflow_graph.py 참조)"""
        print("\n[Data Extraction] Extracting chart data via JavaScript...")
        
        try:
            chart_selector = "#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-body > div > div > div.StatisticsIndicators__chart-wrap__4UCu\\+.StatisticsIndicators__chart-wrap-m__b8qFo"
            
            chart_data_result = await page.evaluate(
                """
                (chartSelector) => {
                    const chartContainer = document.querySelector(chartSelector);
                    if (!chartContainer) return { error: 'Chart container not found' };
                    
                    const canvas = chartContainer.querySelector('canvas');
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
                    
                    // React Fiber - 더 깊이 탐색
                    const reactKey = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                    if (reactKey) {
                        let fiber = canvas[reactKey];
                        const visited = new Set();
                        
                        // 부모로 올라가며 탐색
                        for (let i = 0; i < 300 && fiber; i++) {
                            if (visited.has(fiber)) break;
                            visited.add(fiber);
                            
                            // props 확인
                            if (fiber.memoizedProps) {
                                const props = fiber.memoizedProps;
                                
                                // Chart.js 데이터 구조
                                if (props.data && props.data.labels && props.data.datasets) {
                                    result.source = 'React (Chart.js props.data)';
                                    result.labels = props.data.labels;
                                    result.datasets = props.data.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                                
                                // options.data 확인
                                if (props.options && props.options.data) {
                                    if (props.options.data.labels && props.options.data.datasets) {
                                        result.source = 'React (options.data)';
                                        result.labels = props.options.data.labels;
                                        result.datasets = props.options.data.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
                                }
                                
                                // chartData 확인
                                if (props.chartData && props.chartData.labels && props.chartData.datasets) {
                                    result.source = 'React (chartData)';
                                    result.labels = props.chartData.labels;
                                    result.datasets = props.chartData.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                                
                                // data 배열 직접 확인
                                if (props.data && Array.isArray(props.data) && props.data.length > 0) {
                                    result.source = 'React (props.data array)';
                                    result.data = props.data;
                                    return result;
                                }
                                
                                // datasets 배열 직접 확인
                                if (props.datasets && Array.isArray(props.datasets) && props.datasets.length > 0) {
                                    result.source = 'React (props.datasets)';
                                    result.datasets = props.datasets;
                                    if (props.labels) result.labels = props.labels;
                                    return result;
                                }
                            }
                            
                            // state 확인
                            if (fiber.memoizedState) {
                                let state = fiber.memoizedState;
                                let stateDepth = 0;
                                while (state && stateDepth < 50) {
                                    if (state.memoizedState) {
                                        const stateData = state.memoizedState;
                                        
                                        if (stateData.data && stateData.data.labels && stateData.data.datasets) {
                                            result.source = 'React (memoizedState.data)';
                                            result.labels = stateData.data.labels;
                                            result.datasets = stateData.data.datasets.map(ds => ({
                                                label: ds.label,
                                                data: ds.data
                                            }));
                                            return result;
                                        }
                                        
                                        if (stateData.chartData && stateData.chartData.labels && stateData.chartData.datasets) {
                                            result.source = 'React (memoizedState.chartData)';
                                            result.labels = stateData.chartData.labels;
                                            result.datasets = stateData.chartData.datasets.map(ds => ({
                                                label: ds.label,
                                                data: ds.data
                                            }));
                                            return result;
                                        }
                                        
                                        if (stateData.data && Array.isArray(stateData.data) && stateData.data.length > 0) {
                                            result.source = 'React (memoizedState.data array)';
                                            result.data = stateData.data;
                                            return result;
                                        }
                                    }
                                    
                                    state = state.next;
                                    stateDepth++;
                                }
                            }
                            
                            // child로도 탐색
                            if (fiber.child) {
                                let child = fiber.child;
                                let childDepth = 0;
                                while (child && childDepth < 50) {
                                    if (child.memoizedProps) {
                                        const childProps = child.memoizedProps;
                                        if (childProps.data && childProps.data.labels && childProps.data.datasets) {
                                            result.source = 'React (child.props.data)';
                                            result.labels = childProps.data.labels;
                                            result.datasets = childProps.data.datasets.map(ds => ({
                                                label: ds.label,
                                                data: ds.data
                                            }));
                                            return result;
                                        }
                                    }
                                    child = child.sibling;
                                    childDepth++;
                                }
                            }
                            
                            fiber = fiber.return;
                        }
                    }
                    
                    // 차트 컨테이너에서 React Fiber 탐색
                    const containerReactKey = Object.keys(chartContainer).find(key => key.startsWith('__reactFiber'));
                    if (containerReactKey) {
                        let containerFiber = chartContainer[containerReactKey];
                        const visited = new Set();
                        
                        for (let i = 0; i < 200 && containerFiber; i++) {
                            if (visited.has(containerFiber)) break;
                            visited.add(containerFiber);
                            
                            if (containerFiber.memoizedProps) {
                                const props = containerFiber.memoizedProps;
                                if (props.data && props.data.labels && props.data.datasets) {
                                    result.source = 'React (container.props.data)';
                                    result.labels = props.data.labels;
                                    result.datasets = props.data.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                            }
                            
                            containerFiber = containerFiber.return;
                        }
                    }
                    
                    // 차트 컨테이너에서 Vue 찾기
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
                    
                    result.error = 'No chart data found in any known structure';
                    return result;
                }
                """,
                chart_selector
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
                        for (let dataset of datasets) {
                            if (dataset && dataset.data) {
                                for (let i = 0; i < labels.length && i < dataset.data.length; i++) {
                                    parsed_data.push({
                                        label: labels[i],
                                        value: dataset.data[i],
                                        dataset_label: dataset.label || 'default',
                                        point_index: i
                                    });
                                }
                            }
                        }
                    } else if (chartDataResult.data && Array.isArray(chartDataResult.data)) {
                        const dataArray = chartDataResult.data;
                        for (let i = 0; i < dataArray.length; i++) {
                            parsed_data.push({
                                point_index: i,
                                value: dataArray[i]
                            });
                        }
                    }
                    
                    for (let item of parsed_data) {
                        time_based_data.push({
                            point_index: item.point_index,
                            label: item.label || null,
                            value: item.value !== undefined ? item.value : null,
                            dataset_label: item.dataset_label || null,
                            tooltip_text: item.label && item.value !== null ? 
                                (item.label + ' ' + item.value) : 
                                (item.value !== null ? String(item.value) : null)
                        });
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
                    print(f"  ✓ Parsed {len(time_based_data)} data points")
                    for i, item in enumerate(time_based_data[:3]):
                        if item.get('value') is not None:
                            print(f"    - {item.get('label', 'Point ' + str(item.get('point_index')))}: {item.get('value')}")
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
        
        self.network_responses = []
        
        async def handle_response(response):
            url = response.url
            if any(keyword in url.lower() for keyword in ['statistics', 'chart', 'data', 'api', 'booking']):
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
        print("\n[Scraping] Starting booking trend chart scraping...")
        
        await self.setup_network_interception(page)
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        
        if not await self.wait_for_chart_load(page):
            print("  ⚠ Chart may not be fully loaded, continuing anyway...")
        
        await asyncio.sleep(3)
        
        # 체크박스 피쳐 목록 가져오기
        features = await self.get_checkbox_features(page)
        
        if not features:
            print("  ⚠ No checkbox features found, extracting default chart data...")
            js_data = await self.extract_chart_data_via_js(page)
            hover_data = await self.extract_chart_data_via_hover(page) if not js_data.get("time_based_data") else []
            
            result = {
                "url": self.stats_url,
                "scraped_at": datetime.now().isoformat(),
                "hover_data": hover_data,
                "js_data": js_data,
                "page_title": await page.title(),
            }
            return result
        
        # 각 체크박스별로 데이터 수집 (테스트: 첫 번째 체크박스만)
        all_feature_data = {}
        
        # 테스트: 첫 번째 체크박스만 처리
        test_mode = True
        features_to_process = features[:1] if test_mode else features
        
        for idx, feature_info in enumerate(features_to_process):
            feature_name = feature_info.get('feature', f'feature_{idx}')
            print(f"\n[Feature {idx + 1}/{len(features_to_process)}] Processing: {feature_name}")
            
            # 체크박스 활성화
            checkbox_toggled = await self.toggle_checkbox(page, idx)
            if not checkbox_toggled:
                print(f"  ⚠ Failed to toggle checkbox, skipping {feature_name}")
                all_feature_data[feature_name] = {
                    "hover_data": [],
                    "js_data": {},
                    "error": "Checkbox toggle failed"
                }
                continue
            
            await asyncio.sleep(3)  # 차트 업데이트 대기
            
            # 차트 데이터 추출
            js_data = await self.extract_chart_data_via_js(page)
            
            # JavaScript 추출 결과 확인
            print(f"  [JS Data Check] Raw data: {js_data.get('raw_data', {})}")
            print(f"  [JS Data Check] Parsed data: {len(js_data.get('parsed_data', []))} items")
            print(f"  [JS Data Check] Time-based data: {len(js_data.get('time_based_data', []))} items")
            
            if not js_data.get("time_based_data") or len(js_data.get("time_based_data", [])) == 0:
                print(f"  ⚠ JS extraction found no data for {feature_name}, trying hover method...")
                hover_data = await self.extract_chart_data_via_hover(page)
                print(f"  [Hover Data Check] Extracted {len(hover_data)} points")
            else:
                hover_data = js_data.get("time_based_data", [])
                print(f"  ✓ Using data from JS extraction ({len(hover_data)} points)")
            
            all_feature_data[feature_name] = {
                "hover_data": hover_data,
                "js_data": js_data,
            }
        
        # 모든 피쳐 데이터를 하나의 리스트로 결합 (join)
        combined_data = []
        max_points = max(
            len(feat_data.get("hover_data", [])) 
            for feat_data in all_feature_data.values()
        ) if all_feature_data else 0
        
        for point_idx in range(max_points):
            row_data = {
                "point_index": point_idx,
            }
            
            for feature_name, feat_data in all_feature_data.items():
                hover_data = feat_data.get("hover_data", [])
                if point_idx < len(hover_data):
                    point_data = hover_data[point_idx]
                    # 피쳐명을 컬럼명으로 사용
                    row_data[f"{feature_name}_value"] = point_data.get("value")
                    row_data[f"{feature_name}_label"] = point_data.get("label")
                    row_data[f"{feature_name}_tooltip"] = point_data.get("tooltip_text")
                else:
                    row_data[f"{feature_name}_value"] = None
                    row_data[f"{feature_name}_label"] = None
                    row_data[f"{feature_name}_tooltip"] = None
            
            combined_data.append(row_data)
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "features": [f.get('feature') for f in features],
            "feature_data": all_feature_data,
            "combined_data": combined_data,
            "hover_data": combined_data,  # CSV 저장을 위해
            "network_responses": [{"url": r["url"], "status": r["status"]} for r in self.network_responses],
            "page_title": await page.title(),
        }
        
        if self.network_responses:
            result["network_data_details"] = self.network_responses[:5]
        
        return result

