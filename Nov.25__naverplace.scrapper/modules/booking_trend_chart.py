#!/usr/bin/env python3
"""
네이버 스마트플레이스 예약 주문 예약 트렌드 차트 데이터 스크래퍼 모듈
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
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
        """특정 체크박스를 활성화하고 차트 업데이트 대기"""
        try:
            # label을 클릭하는 방식으로 변경 (input이 disabled일 수 있음)
            label_selector = f"#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})"
            
            # label이 나타날 때까지 대기
            await page.wait_for_selector(label_selector, timeout=10000)
            await asyncio.sleep(1)
            
            # 체크박스 클릭 전 차트 데이터 스냅샷 (업데이트 확인용)
            chart_snapshot_before = await page.evaluate(
                """
                () => {
                    // CanvasJS 차트 인스턴스 찾기
                    if (window.CanvasJS && window.CanvasJS.Chart) {
                        const charts = window.CanvasJS.Chart.charts || [];
                        if (charts.length > 0) {
                            const chart = charts[0];
                            if (chart.options && chart.options.data) {
                                return {
                                    found: true,
                                    dataPointsCount: chart.options.data[0]?.dataPoints?.length || 0,
                                    dataHash: JSON.stringify(chart.options.data).substring(0, 100)
                                };
                            }
                        }
                    }
                    // Chart.js 인스턴스 찾기
                    if (window.Chart && window.Chart.instances) {
                        const chartIds = Object.keys(window.Chart.instances);
                        if (chartIds.length > 0) {
                            const chart = window.Chart.instances[chartIds[0]];
                            if (chart.data && chart.data.datasets) {
                                return {
                                    found: true,
                                    dataPointsCount: chart.data.datasets[0]?.data?.length || 0,
                                    dataHash: JSON.stringify(chart.data).substring(0, 100)
                                };
                            }
                        }
                    }
                    return { found: false };
                }
                """
            )
            
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
                # 차트 업데이트 대기 (CanvasJS 방식: render() 호출 확인 또는 데이터 변경 감지)
                await asyncio.sleep(1)  # 초기 대기
                
                # 차트가 업데이트될 때까지 대기 (최대 5초)
                for attempt in range(10):
                    chart_snapshot_after = await page.evaluate(
                        """
                        () => {
                            // CanvasJS 차트 인스턴스 찾기
                            if (window.CanvasJS && window.CanvasJS.Chart) {
                                const charts = window.CanvasJS.Chart.charts || [];
                                if (charts.length > 0) {
                                    const chart = charts[0];
                                    if (chart.options && chart.options.data) {
                                        return {
                                            found: true,
                                            dataPointsCount: chart.options.data[0]?.dataPoints?.length || 0,
                                            dataHash: JSON.stringify(chart.options.data).substring(0, 100)
                                        };
                                    }
                                }
                            }
                            // Chart.js 인스턴스 찾기
                            if (window.Chart && window.Chart.instances) {
                                const chartIds = Object.keys(window.Chart.instances);
                                if (chartIds.length > 0) {
                                    const chart = window.Chart.instances[chartIds[0]];
                                    if (chart.data && chart.data.datasets) {
                                        return {
                                            found: true,
                                            dataPointsCount: chart.data.datasets[0]?.data?.length || 0,
                                            dataHash: JSON.stringify(chart.data).substring(0, 100)
                                        };
                                    }
                                }
                            }
                            return { found: false };
                        }
                        """
                    )
                    
                    # 차트 데이터가 변경되었는지 확인
                    if chart_snapshot_before.get('found') and chart_snapshot_after.get('found'):
                        if (chart_snapshot_before.get('dataHash') != chart_snapshot_after.get('dataHash') or
                            chart_snapshot_before.get('dataPointsCount') != chart_snapshot_after.get('dataPointsCount')):
                            print(f"  ✓ Checkbox {checkbox_index} toggled - Chart data updated")
                            return True
                    
                    await asyncio.sleep(0.5)
                
                # 차트 업데이트가 감지되지 않았지만 체크박스는 클릭됨
                print(f"  ✓ Checkbox {checkbox_index} toggled (chart update not detected, continuing...)")
                await asyncio.sleep(2)  # 추가 대기
                return True
            else:
                print(f"  ⚠ Failed to toggle checkbox {checkbox_index}")
                return False
                
        except Exception as e:
            print(f"  ⚠ Error toggling checkbox {checkbox_index}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def uncheck_checkbox(self, page: Page, checkbox_index: int) -> bool:
        """특정 체크박스가 체크되어 있으면 해제"""
        try:
            label_selector = f"#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})"
            
            current_state = await page.evaluate(
                f"""
                () => {{
                    const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                    if (!label) return {{found: false}};
                    const input = label.querySelector('input.check-radio');
                    if (!input) return {{found: false}};
                    return {{found: true, checked: input.checked}};
                }}
                """
            )
            
            if not current_state.get('found') or not current_state.get('checked'):
                return True  # 이미 해제되어 있음
            
            # 체크박스 클릭하여 해제
            try:
                await page.evaluate(
                    f"""
                    () => {{
                        const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                        if (label) {{
                            const input = label.querySelector('input.check-radio');
                            if (input && input.checked) {{
                                label.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}
                    """
                )
                await asyncio.sleep(0.3)
                return True
            except Exception:
                return False
            
        except Exception:
            return False
    
    async def ensure_checkbox_checked(self, page: Page, checkbox_index: int) -> bool:
        """특정 체크박스가 체크되어 있는지 확인하고, 체크되어 있지 않으면 체크"""
        try:
            label_selector = f"#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})"
            
            await page.wait_for_selector(label_selector, timeout=10000)
            await asyncio.sleep(1)
            
            # 현재 상태 확인
            current_state = await page.evaluate(
                f"""
                () => {{
                    const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                    if (!label) return {{found: false}};
                    const input = label.querySelector('input.check-radio');
                    if (!input) return {{found: false}};
                    return {{found: true, checked: input.checked}};
                }}
                """
            )
            
            if not current_state.get('found'):
                return False
            
            # 이미 체크되어 있으면 그대로 유지
            if current_state.get('checked', False):
                await asyncio.sleep(1)
                return True
            
            # 체크되어 있지 않으면 클릭하여 체크
            try:
                await page.evaluate(
                    f"""
                    () => {{
                        const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                        if (label) {{
                            label.click();
                            return true;
                        }}
                        return false;
                    }}
                    """
                )
                await asyncio.sleep(0.5)
            except Exception:
                return False
            
            # 클릭 후 상태 확인
            await asyncio.sleep(1)
            after_state = await page.evaluate(
                f"""
                () => {{
                    const label = document.querySelector('#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-footer.StatisticsIndicators__statistics-footer-group__nyT3T > div > label:nth-child({checkbox_index + 1})');
                    if (!label) return {{found: false}};
                    const input = label.querySelector('input.check-radio');
                    return {{found: !!input, checked: input?.checked || false}};
                }}
                """
            )
            
            if after_state.get('found') and after_state.get('checked', False):
                return True
            return False
                
        except Exception as e:
            print(f"  ⚠ Error ensuring checkbox {checkbox_index} is checked: {e}")
            return False
    
    async def extract_chart_data_via_hover(self, page: Page) -> list:
        """그래프에 롤오버하여 데이터 추출 (fallback 방식 - JS 추출 실패 시에만 사용)"""
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
                                            const hasDate = /\\d{4}-\\d{2}-\\d{2}|\\d{1,2}\\/\\d{1,2}|\\d{1,2}일/.test(text);
                                            const hasNumber = /\\d/.test(text);
                                            
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
                                                
                                                const hasDate = /\\d{4}-\\d{2}-\\d{2}|\\d{1,2}\\/\\d{1,2}|\\d{1,2}일/.test(text);
                                                const hasNumber = /\\d/.test(text);
                                                
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
    
    async def extract_props_data_simple(self, page: Page) -> dict:
        """React props.data에서 차트 데이터 간단하게 추출 (체크박스 변경 시 업데이트됨)"""
        print("\n[Data Extraction] Extracting chart data from React props.data...")
        
        try:
            result = await page.evaluate(
                """
                () => {
                    // 여러 선택자 시도 (우선순위 순)
                    const selectors = [
                        '[class*="chart-wrap"] canvas',
                        '.panel-body canvas',
                        'canvas'
                    ];
                    
                    let canvas = null;
                    let usedSelector = null;
                    for (const selector of selectors) {
                        canvas = document.querySelector(selector);
                        if (canvas) {
                            usedSelector = selector;
                            break;
                        }
                    }
                    
                    if (!canvas) return { error: 'Canvas not found', selectors: selectors };
                    
                    const fiberKey = Object.keys(canvas).find(k => k.startsWith('__reactFiber'));
                    if (!fiberKey) return { error: 'React Fiber not found', selector: usedSelector };
                    
                    let fiber = canvas[fiberKey];
                    let depth = 0;
                    let foundProps = [];
                    
                    // 깊이 늘리기 (10 -> 30)
                    while (fiber && depth < 30) {
                        if (fiber.memoizedProps) {
                            const props = fiber.memoizedProps;
                            
                            // props.data가 배열이고 첫 번째 요소도 배열인 경우
                            if (props.data && Array.isArray(props.data) && props.data.length > 0) {
                                const data = props.data;
                                
                                // props.data 구조: [['피쳐명', 값1, 값2, ...], ['피쳐명2', 값1, 값2, ...], ...]
                                if (Array.isArray(data[0]) && data[0].length > 1 && typeof data[0][0] === 'string') {
                                    const labels = props.label || [];
                                    const datasets = data.map(series => ({
                                        feature_name: series[0],
                                        values: series.slice(1)
                                    }));
                                    
                                    return {
                                        found: true,
                                        source: 'React props.data',
                                        labels: labels,
                                        datasets: datasets,
                                        seriesCount: data.length,
                                        depth: depth,
                                        selector: usedSelector
                                    };
                                }
                                
                                // 다른 형태의 데이터 구조도 기록
                                foundProps.push({
                                    depth: depth,
                                    dataLength: data.length,
                                    firstItemType: typeof data[0],
                                    isFirstItemArray: Array.isArray(data[0])
                                });
                            }
                        }
                        fiber = fiber.return;
                        depth++;
                    }
                    
                    return { 
                        error: 'props.data not found', 
                        depth: depth, 
                        selector: usedSelector,
                        foundProps: foundProps
                    };
                }
                """
            )
            
            if result.get('error'):
                print(f"  ⚠ {result.get('error')}")
                if result.get('selector'):
                    print(f"    Selector used: {result.get('selector')}")
                if result.get('foundProps'):
                    print(f"    Found props at depths: {result.get('foundProps')}")
                return {"time_based_data": [], "error": result.get('error')}
            
            print(f"  ✓ Found data at depth {result.get('depth')}: {result.get('seriesCount')} series")
            print(f"    Selector: {result.get('selector')}")
            
            # 파싱: datasets를 time_based_data 형식으로 변환
            time_based_data = []
            labels = result.get('labels', [])
            datasets = result.get('datasets', [])
            
            for dataset in datasets:
                feature_name = dataset.get('feature_name', 'unknown')
                values = dataset.get('values', [])
                
                for i, value in enumerate(values):
                    label = labels[i] if i < len(labels) else None
                    # labels가 중첩 배열인 경우 처리 (예: [['12월', '01일'], ['12월', '02일'], ...])
                    if label and isinstance(label, list):
                        label = ' '.join(str(l) for l in label)
                    
                    time_based_data.append({
                        'point_index': i,
                        'label': label,
                        'value': value,
                        'feature_name': feature_name,
                        'dataset_label': feature_name
                    })
                
                print(f"    - {feature_name}: {len(values)} points")
            
            return {
                "source": result.get('source'),
                "time_based_data": time_based_data,
                "labels": labels,
                "datasets": datasets
            }
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return {"time_based_data": [], "error": str(e)}
    
    async def extract_chart_data_via_js(self, page: Page) -> dict:
        """JavaScript를 사용하여 차트 데이터 직접 추출 (place_hourly_inflow_graph.py 참조)"""
        print("\n[Data Extraction] Extracting chart data via JavaScript...")
        
        try:
            chart_selector = "#app > div > div.BaseLayout__container__L0brn > div.BaseLayout__contents__k3cMt > div > div > div.StatisticsIndicators__statistic-contents-out-scroll__MoPQ5 > div.StatisticsIndicators__statistic-contents-in__sFa1a > div:nth-child(3) > div.panel-body > div > div > div.StatisticsIndicators__chart-wrap__4UCu\\+.StatisticsIndicators__chart-wrap-m__b8qFo"
            
            # 먼저 디버깅 정보 수집
            debug_info = await page.evaluate(
                """
                (chartSelector) => {
                    const chartContainer = document.querySelector(chartSelector);
                    const debug = {
                        containerFound: !!chartContainer,
                        canvasFound: false,
                        chartLibraries: [],
                        reactFound: false,
                        vueFound: false,
                        angularFound: false,
                        echartsFound: false,
                        canvasJSFound: false
                    };
                    
                    if (chartContainer) {
                        const canvas = chartContainer.querySelector('canvas');
                        debug.canvasFound = !!canvas;
                        
                        // CanvasJS 확인
                        if (window.CanvasJS && window.CanvasJS.Chart) {
                            debug.chartLibraries.push('CanvasJS');
                            debug.canvasJSFound = true;
                            const charts = window.CanvasJS.Chart.charts || [];
                            debug.canvasJSInstances = charts.length;
                            if (charts.length > 0) {
                                debug.canvasJSDataPoints = charts[0].options?.data?.[0]?.dataPoints?.length || 0;
                            }
                        }
                        
                        // Chart.js 확인
                        if (window.Chart) {
                            debug.chartLibraries.push('Chart.js');
                            if (window.Chart.instances) {
                                debug.chartInstances = Object.keys(window.Chart.instances).length;
                            }
                        }
                        
                        // React 확인
                        if (canvas) {
                            const reactKey = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                            debug.reactFound = !!reactKey;
                            
                            const vueKey = Object.keys(canvas).find(key => key.startsWith('__vue'));
                            debug.vueFound = !!vueKey;
                            
                            const ngKey = Object.keys(canvas).find(key => key.startsWith('__ngContext'));
                            debug.angularFound = !!ngKey;
                            
                            const ecKey = Object.keys(canvas).find(key => key === '__ec__');
                            debug.echartsFound = !!ecKey;
                        }
                    }
                    
                    return debug;
                }
                """,
                chart_selector
            )
            
            if debug_info:
                print(f"  [Debug] Container found: {debug_info.get('containerFound')}")
                print(f"  [Debug] Canvas found: {debug_info.get('canvasFound')}")
                print(f"  [Debug] Chart libraries: {debug_info.get('chartLibraries', [])}")
                print(f"  [Debug] React: {debug_info.get('reactFound')}, Vue: {debug_info.get('vueFound')}, Angular: {debug_info.get('angularFound')}, ECharts: {debug_info.get('echartsFound')}, CanvasJS: {debug_info.get('canvasJSFound')}")
                if debug_info.get('chartInstances'):
                    print(f"  [Debug] Chart.js instances: {debug_info.get('chartInstances')}")
                if debug_info.get('canvasJSInstances'):
                    print(f"  [Debug] CanvasJS instances: {debug_info.get('canvasJSInstances')}")
                    if debug_info.get('canvasJSDataPoints'):
                        print(f"  [Debug] CanvasJS data points: {debug_info.get('canvasJSDataPoints')}")
            
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
                        error: null,
                        debug: {}
                    };
                    
                    // CanvasJS - 체크박스 변경 후 데이터 추출
                    if (window.CanvasJS && window.CanvasJS.Chart) {
                        // CanvasJS.Chart.charts 배열에서 차트 인스턴스 찾기
                        const charts = window.CanvasJS.Chart.charts || [];
                        for (let chart of charts) {
                            if (chart.options && chart.options.data && chart.options.data.length > 0) {
                                const dataSeries = chart.options.data[0];
                                if (dataSeries.dataPoints && Array.isArray(dataSeries.dataPoints)) {
                                    result.source = 'CanvasJS (chart.options.data[0].dataPoints)';
                                    result.labels = dataSeries.dataPoints.map(dp => dp.label || dp.x);
                                    result.datasets = [{
                                        label: dataSeries.name || dataSeries.legendText || 'default',
                                        data: dataSeries.dataPoints.map(dp => dp.y || dp.value)
                                    }];
                                    return result;
                                }
                            }
                        }
                        // 차트 컨테이너에서 CanvasJS 인스턴스 찾기
                        const containerCanvasJS = chartContainer.__canvasjsChart || canvas.__canvasjsChart;
                        if (containerCanvasJS && containerCanvasJS.options) {
                            const dataSeries = containerCanvasJS.options.data && containerCanvasJS.options.data[0];
                            if (dataSeries && dataSeries.dataPoints) {
                                result.source = 'CanvasJS (container.__canvasjsChart)';
                                result.labels = dataSeries.dataPoints.map(dp => dp.label || dp.x);
                                result.datasets = [{
                                    label: dataSeries.name || 'default',
                                    data: dataSeries.dataPoints.map(dp => dp.y || dp.value)
                                }];
                                return result;
                            }
                        }
                    }
                    
                    // React Fiber에서 props.data와 props.label 찾기 (우선순위 높음 - 체크박스 변경 시 업데이트됨)
                    const reactFiberKey = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                    if (reactFiberKey) {
                        let fiber = canvas[reactFiberKey];
                        let depth = 0;
                        
                        while (fiber && depth < 5) {
                            if (fiber.memoizedProps) {
                                const props = fiber.memoizedProps;
                                
                                // props.data와 props.label 찾기 (배열 구조: [['피쳐명', 값1, 값2, ...], ...])
                                if (props.data && Array.isArray(props.data) && props.data.length > 0) {
                                    const data = props.data;
                                    // 첫 번째 요소가 배열이고 첫 번째 요소가 문자열(피쳐명)인 경우
                                    if (Array.isArray(data[0]) && typeof data[0][0] === 'string') {
                                        result.source = 'React (props.data + props.label)';
                                        result.labels = props.label || [];
                                        
                                        // 각 시리즈를 dataset으로 변환
                                        result.datasets = data.map((series, idx) => {
                                            const featureName = series[0]; // 첫 번째 요소가 피쳐명
                                            const values = series.slice(1); // 나머지가 값들
                                            
                                            return {
                                                label: featureName,
                                                data: values,
                                                feature_name: featureName
                                            };
                                        });
                                        
                                        return result;
                                    }
                                }
                            }
                            
                            fiber = fiber.return;
                            depth++;
                        }
                    }
                    
                    // Chart.js - 가장 일반적인 방법
                    if (window.Chart && window.Chart.instances) {
                        const charts = window.Chart.instances;
                        const chartIds = Object.keys(charts);
                        for (let chartId of chartIds) {
                            const chart = charts[chartId];
                            if (chart && chart.data && chart.data.labels && chart.data.datasets) {
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
                    
                    // React Props 직접 접근 (__reactProps 키 확인)
                    const reactPropsKey = Object.keys(canvas).find(key => key.startsWith('__reactProps'));
                    if (reactPropsKey) {
                        const reactProps = canvas[reactPropsKey];
                        if (reactProps) {
                            // data 확인
                            if (reactProps.data && reactProps.data.labels && reactProps.data.datasets) {
                                result.source = 'React (__reactProps.data)';
                                result.labels = reactProps.data.labels;
                                result.datasets = reactProps.data.datasets.map(ds => ({
                                    label: ds.label,
                                    data: ds.data
                                }));
                                return result;
                            }
                            // options.data 확인
                            if (reactProps.options && reactProps.options.data) {
                                if (reactProps.options.data.labels && reactProps.options.data.datasets) {
                                    result.source = 'React (__reactProps.options.data)';
                                    result.labels = reactProps.options.data.labels;
                                    result.datasets = reactProps.options.data.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                            }
                            // chartData 확인
                            if (reactProps.chartData && reactProps.chartData.labels && reactProps.chartData.datasets) {
                                result.source = 'React (__reactProps.chartData)';
                                result.labels = reactProps.chartData.labels;
                                result.datasets = reactProps.chartData.datasets.map(ds => ({
                                    label: ds.label,
                                    data: ds.data
                                }));
                                return result;
                            }
                            // 모든 props 키 탐색
                            for (let key in reactProps) {
                                const value = reactProps[key];
                                if (value && typeof value === 'object') {
                                    // labels와 datasets를 가진 객체 찾기
                                    if (value.labels && value.datasets && Array.isArray(value.labels) && Array.isArray(value.datasets)) {
                                        result.source = `React (__reactProps.${key})`;
                                        result.labels = value.labels;
                                        result.datasets = value.datasets.map(ds => ({
                                            label: ds.label || key,
                                            data: ds.data || ds
                                        }));
                                        return result;
                                    }
                                    // data 배열을 가진 객체 찾기
                                    if (value.data && Array.isArray(value.data) && value.data.length > 0) {
                                        result.source = `React (__reactProps.${key}.data)`;
                                        result.data = value.data;
                                        if (value.labels) result.labels = value.labels;
                                        return result;
                                    }
                                }
                            }
                        }
                    }
                    
                    // 차트 컨테이너의 React Props도 확인
                    const containerReactPropsKey = Object.keys(chartContainer).find(key => key.startsWith('__reactProps'));
                    if (containerReactPropsKey) {
                        const containerReactProps = chartContainer[containerReactPropsKey];
                        if (containerReactProps) {
                            // data 확인
                            if (containerReactProps.data && containerReactProps.data.labels && containerReactProps.data.datasets) {
                                result.source = 'React (container.__reactProps.data)';
                                result.labels = containerReactProps.data.labels;
                                result.datasets = containerReactProps.data.datasets.map(ds => ({
                                    label: ds.label,
                                    data: ds.data
                                }));
                                return result;
                            }
                            // 모든 props 키 탐색
                            for (let key in containerReactProps) {
                                const value = containerReactProps[key];
                                if (value && typeof value === 'object') {
                                    if (value.labels && value.datasets && Array.isArray(value.labels) && Array.isArray(value.datasets)) {
                                        result.source = `React (container.__reactProps.${key})`;
                                        result.labels = value.labels;
                                        result.datasets = value.datasets.map(ds => ({
                                            label: ds.label || key,
                                            data: ds.data || ds
                                        }));
                                        return result;
                                    }
                                }
                            }
                        }
                    }
                    
                    // React Fiber - canvas에서 시작 (더 깊이 탐색)
                    const reactFiberKeyDeep = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                    if (reactFiberKeyDeep) {
                        let fiber = canvas[reactFiberKeyDeep];
                        const visited = new Set();
                        
                        // 부모로 올라가며 탐색 (최대 200단계로 증가)
                        for (let i = 0; i < 200 && fiber; i++) {
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
                                
                                // chartOptions 확인
                                if (props.chartOptions && props.chartOptions.data) {
                                    if (props.chartOptions.data.labels && props.chartOptions.data.datasets) {
                                        result.source = 'React (chartOptions.data)';
                                        result.labels = props.chartOptions.data.labels;
                                        result.datasets = props.chartOptions.data.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
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
                                
                                // 더 많은 가능한 구조 탐색
                                for (let key in props) {
                                    const value = props[key];
                                    if (value && typeof value === 'object') {
                                        // labels와 datasets를 가진 객체 찾기
                                        if (value.labels && value.datasets && Array.isArray(value.labels) && Array.isArray(value.datasets)) {
                                            result.source = `React (props.${key})`;
                                            result.labels = value.labels;
                                            result.datasets = value.datasets.map(ds => ({
                                                label: ds.label || key,
                                                data: ds.data || ds
                                            }));
                                            return result;
                                        }
                                        // data 배열을 가진 객체 찾기
                                        if (value.data && Array.isArray(value.data) && value.data.length > 0) {
                                            result.source = `React (props.${key}.data)`;
                                            result.data = value.data;
                                            if (value.labels) result.labels = value.labels;
                                            return result;
                                        }
                                    }
                                }
                            }
                            
                            // stateNode 확인 (클래스 컴포넌트의 경우)
                            if (fiber.stateNode) {
                                const stateNode = fiber.stateNode;
                                // stateNode의 state 확인
                                if (stateNode.state) {
                                    const nodeState = stateNode.state;
                                    if (nodeState.data && nodeState.data.labels && nodeState.data.datasets) {
                                        result.source = 'React (stateNode.state.data)';
                                        result.labels = nodeState.data.labels;
                                        result.datasets = nodeState.data.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
                                    if (nodeState.chartData && nodeState.chartData.labels && nodeState.chartData.datasets) {
                                        result.source = 'React (stateNode.state.chartData)';
                                        result.labels = nodeState.chartData.labels;
                                        result.datasets = nodeState.chartData.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
                                }
                                // stateNode의 props 확인
                                if (stateNode.props) {
                                    const nodeProps = stateNode.props;
                                    if (nodeProps.data && nodeProps.data.labels && nodeProps.data.datasets) {
                                        result.source = 'React (stateNode.props.data)';
                                        result.labels = nodeProps.data.labels;
                                        result.datasets = nodeProps.data.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
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
                    
                    // 차트 컨테이너에서 React Fiber 탐색 (더 깊이)
                    const containerReactKey = Object.keys(chartContainer).find(key => key.startsWith('__reactFiber'));
                    if (containerReactKey) {
                        let containerFiber = chartContainer[containerReactKey];
                        const visited = new Set();
                        
                        for (let i = 0; i < 300 && containerFiber; i++) {
                            if (visited.has(containerFiber)) break;
                            visited.add(containerFiber);
                            
                            if (containerFiber.memoizedProps) {
                                const props = containerFiber.memoizedProps;
                                
                                // 기본 데이터 구조
                                if (props.data && props.data.labels && props.data.datasets) {
                                    result.source = 'React (container.props.data)';
                                    result.labels = props.data.labels;
                                    result.datasets = props.data.datasets.map(ds => ({
                                        label: ds.label,
                                        data: ds.data
                                    }));
                                    return result;
                                }
                                
                                // 모든 props 키 탐색
                                for (let key in props) {
                                    const value = props[key];
                                    if (value && typeof value === 'object') {
                                        // labels와 datasets를 가진 객체 찾기
                                        if (value.labels && value.datasets && Array.isArray(value.labels) && Array.isArray(value.datasets)) {
                                            result.source = `React (container.props.${key})`;
                                            result.labels = value.labels;
                                            result.datasets = value.datasets.map(ds => ({
                                                label: ds.label || key,
                                                data: ds.data || ds
                                            }));
                                            return result;
                                        }
                                        // data 배열을 가진 객체 찾기
                                        if (value.data && Array.isArray(value.data) && value.data.length > 0) {
                                            result.source = `React (container.props.${key}.data)`;
                                            result.data = value.data;
                                            if (value.labels) result.labels = value.labels;
                                            return result;
                                        }
                                    }
                                }
                            }
                            
                            // state도 확인
                            if (containerFiber.memoizedState) {
                                let state = containerFiber.memoizedState;
                                let stateDepth = 0;
                                while (state && stateDepth < 100) {
                                    if (state.memoizedState) {
                                        const stateData = state.memoizedState;
                                        if (stateData.data && stateData.data.labels && stateData.data.datasets) {
                                            result.source = 'React (container.memoizedState.data)';
                                            result.labels = stateData.data.labels;
                                            result.datasets = stateData.data.datasets.map(ds => ({
                                                label: ds.label,
                                                data: ds.data
                                            }));
                                            return result;
                                        }
                                    }
                                    state = state.next;
                                    stateDepth++;
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
                    
                    // 차트 컨테이너에서 Angular 찾기
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
                    
                    // 데이터를 찾지 못한 경우 디버깅 정보 수집
                    // 이미 선언된 변수 재사용 (reactPropsKey, containerReactPropsKey는 위에서 선언됨)
                    // React Props의 키 목록 수집 (데이터 구조 파악용)
                    let reactPropsKeys = [];
                    let containerReactPropsKeys = [];
                    
                    // canvas의 reactPropsKey 재확인
                    const canvasReactPropsKeyForDebug = Object.keys(canvas).find(key => key.startsWith('__reactProps'));
                    if (canvasReactPropsKeyForDebug) {
                        const reactProps = canvas[canvasReactPropsKeyForDebug];
                        if (reactProps) {
                            reactPropsKeys = Object.keys(reactProps).slice(0, 20); // 처음 20개만
                        }
                    }
                    
                    // container의 reactPropsKey 재확인
                    const containerReactPropsKeyForDebug = Object.keys(chartContainer).find(key => key.startsWith('__reactProps'));
                    if (containerReactPropsKeyForDebug) {
                        const containerReactProps = chartContainer[containerReactPropsKeyForDebug];
                        if (containerReactProps) {
                            containerReactPropsKeys = Object.keys(containerReactProps).slice(0, 20);
                        }
                    }
                    
                    // React Fiber 키 확인 (여러 곳에서 선언되었으므로 각각 확인)
                    const reactFiberKeyForDebug = Object.keys(canvas).find(key => key.startsWith('__reactFiber'));
                    
                    result.debug = {
                        chartContainerKeys: Object.keys(chartContainer).filter(k => k.startsWith('__')),
                        canvasKeys: canvas ? Object.keys(canvas).filter(k => k.startsWith('__')) : [],
                        hasChartJs: !!window.Chart,
                        chartJsInstances: window.Chart && window.Chart.instances ? Object.keys(window.Chart.instances).length : 0,
                        hasCanvasJS: !!(window.CanvasJS && window.CanvasJS.Chart),
                        canvasJSInstances: window.CanvasJS && window.CanvasJS.Chart && window.CanvasJS.Chart.charts ? window.CanvasJS.Chart.charts.length : 0,
                        reactFound: !!reactFiberKeyForDebug,
                        reactPropsFound: !!canvasReactPropsKeyForDebug,
                        reactPropsKeys: reactPropsKeys,
                        containerReactPropsKeys: containerReactPropsKeys,
                        vueFound: !!vueKey,
                        angularFound: !!ngKey,
                        echartsFound: !!ecKey
                    };
                    
                    // 마지막 시도: 차트 컨테이너의 모든 자식 요소에서 데이터 찾기
                    const allChildren = chartContainer.querySelectorAll('*');
                    for (let child of allChildren) {
                        const childReactKey = Object.keys(child).find(key => key.startsWith('__reactFiber'));
                        if (childReactKey) {
                            let childFiber = child[childReactKey];
                            const visited = new Set();
                            
                            for (let i = 0; i < 50 && childFiber; i++) {
                                if (visited.has(childFiber)) break;
                                visited.add(childFiber);
                                
                                if (childFiber.memoizedProps) {
                                    const props = childFiber.memoizedProps;
                                    if (props.data && props.data.labels && props.data.datasets) {
                                        result.source = 'React (child element)';
                                        result.labels = props.data.labels;
                                        result.datasets = props.data.datasets.map(ds => ({
                                            label: ds.label,
                                            data: ds.data
                                        }));
                                        return result;
                                    }
                                }
                                
                                childFiber = childFiber.return;
                            }
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
                        // props.data 구조 처리: 각 dataset의 data는 날짜별 값 배열
                        for (let dataset of datasets) {
                            if (dataset && dataset.data && Array.isArray(dataset.data)) {
                                const featureName = dataset.label || dataset.feature_name || 'unknown';
                                for (let i = 0; i < dataset.data.length && i < labels.length; i++) {
                                    parsed_data.push({
                                        label: labels[i],
                                        value: dataset.data[i],
                                        dataset_label: featureName,
                                        feature_name: featureName,
                                        point_index: i
                                    });
                                }
                            }
                        }
                    } else if (chartDataResult.data && Array.isArray(chartDataResult.data)) {
                        const dataArray = chartDataResult.data;
                        // 데이터 구조 확인: 각 요소가 배열인 경우 (예: ['신청', 22, 13, 12, ...])
                        for (let i = 0; i < dataArray.length; i++) {
                            const item = dataArray[i];
                            if (Array.isArray(item) && item.length > 1) {
                                // 첫 번째 요소가 피쳐명, 나머지가 날짜별 값들
                                const featureName = item[0];
                                const values = item.slice(1);
                                
                                // 각 날짜별 값으로 분리
                                for (let j = 0; j < values.length; j++) {
                                    parsed_data.push({
                                        point_index: j,
                                        value: values[j],
                                        dataset_label: featureName,
                                        feature_name: featureName
                                    });
                                }
                            } else {
                                parsed_data.push({
                                    point_index: i,
                                    value: item
                                });
                            }
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
                    # 피쳐별로 그룹화하여 출력
                    features_found = {}
                    for item in time_based_data:
                        feature_name = item.get('feature_name') or item.get('dataset_label') or 'unknown'
                        if feature_name not in features_found:
                            features_found[feature_name] = []
                        features_found[feature_name].append(item)
                    
                    for feature_name, feature_data in features_found.items():
                        print(f"    - {feature_name}: {len(feature_data)} points")
                        # 샘플 출력
                        for i, item in enumerate(feature_data[:2]):
                            if item.get('value') is not None:
                                print(f"      [{i}] {item.get('label', 'N/A')}: {item.get('value')}")
            else:
                error_msg = chart_data_result.get('error') if chart_data_result else 'No data found'
                print(f"  ⚠ {error_msg}")
                
                # 디버깅 정보 출력
                if chart_data_result and chart_data_result.get('debug'):
                    debug_info = chart_data_result.get('debug')
                    print(f"  [Debug] Chart container keys: {debug_info.get('chartContainerKeys', [])[:5]}")
                    print(f"  [Debug] Canvas keys: {debug_info.get('canvasKeys', [])[:5]}")
                    print(f"  [Debug] Chart.js instances: {debug_info.get('chartJsInstances', 0)}")
                    print(f"  [Debug] CanvasJS instances: {debug_info.get('canvasJSInstances', 0)}")
                    print(f"  [Debug] React: {debug_info.get('reactFound')}, ReactProps: {debug_info.get('reactPropsFound')}, Vue: {debug_info.get('vueFound')}, Angular: {debug_info.get('angularFound')}, ECharts: {debug_info.get('echartsFound')}, CanvasJS: {debug_info.get('hasCanvasJS')}")
                    react_props_keys = debug_info.get('reactPropsKeys', [])
                    container_react_props_keys = debug_info.get('containerReactPropsKeys', [])
                    if react_props_keys:
                        print(f"  [Debug] Canvas React Props keys: {react_props_keys[:10]}")
                    else:
                        print(f"  [Debug] Canvas React Props keys: (empty or not found)")
                    if container_react_props_keys:
                        print(f"  [Debug] Container React Props keys: {container_react_props_keys[:10]}")
                    else:
                        print(f"  [Debug] Container React Props keys: (empty or not found)")
            
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
            # reports API만 필터링 (차트 데이터가 포함된 API)
            if '/api/businesses/' in url and '/reports' in url:
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = await response.json()
                        self.network_responses.append({
                            "url": url,
                            "status": response.status,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"  ✓ Captured API response: {url[:80]}...")
                except Exception:
                    pass
        
        page.on("response", handle_response)
    
    async def extract_chart_data_from_api(self, feature_name: str = None, responses_before_count: int = 0) -> list:
        """네트워크 API 응답에서 차트 데이터 추출
        
        Args:
            feature_name: 체크박스 피쳐명
            responses_before_count: 체크박스 체크 전의 응답 수 (새로운 응답만 확인하기 위해)
        """
        print(f"\n[API Extraction] Extracting chart data from API responses...")
        
        chart_data = []
        
        # metric 필드 매핑 (체크박스 변경 시 API 요청이 발생하지 않으므로 metric으로 필터링)
        feature_metric_map = {
            '신청': 'REQUESTED',
            '확정': 'CONFIRMED',
            '취소': 'CANCELLED',  # 모든 취소 타입 포함
            '예약자 취소': 'CANCELLED',
            '사업자 취소': 'CANCELLED',
            '미확정 자동 취소': 'CANCELLED',
            '완료': 'ENDED',
            '변경': 'CHANGED',
            '노쇼': 'NOSHOW'
        }
        
        # 취소 타입 필터링을 위한 설정 (함수 전체에서 사용)
        cancelled_type_map = {
            '예약자 취소': ['예약자 취소', '고객 취소', '예약자'],
            '사업자 취소': ['사업자 취소', '사업자'],
            '미확정 자동 취소': ['사업자 미확정 취소', '미확정']
        }
        
        # 최근 API 응답 중 reports API 찾기
        all_reports_responses = [
            r for r in self.network_responses 
            if '/reports' in r.get('url', '') and r.get('data')
        ]
        
        if not all_reports_responses:
            print("  ⚠ No reports API responses found")
            return chart_data
        
        # 체크박스 체크 후 발생한 새로운 응답만 사용
        reports_responses = all_reports_responses[responses_before_count:]
        
        if not reports_responses:
            print(f"  ⚠ No new API responses after checkbox check (using all responses)")
            reports_responses = all_reports_responses
        
        # bizItemId bucket 제외 (비즈니스 아이템 목록이므로 차트 데이터 아님)
        reports_responses = [
            r for r in reports_responses
            if 'bizItemId' not in r.get('url', '')
        ]
        
        if not reports_responses:
            print("  ⚠ No valid reports API responses found (excluding bizItemId)")
            return chart_data
        
        # 모든 bucket을 확인하고 metric으로 필터링하여 가장 많은 데이터를 가진 응답 선택
        best_response = None
        best_data_count = 0
        bucket_metrics_info = []  # 디버깅용
        
        for response in reports_responses:
            api_data = response.get('data', {})
            url = response.get('url', '')
            
            if 'result' in api_data and isinstance(api_data.get('result'), list):
                result_list = api_data.get('result', [])
                
                # bucket 이름 추출
                bucket_name = 'unknown'
                for bucket in ['day_trend', 'bookingCo', 'cancelled', 'price_sum']:
                    if bucket in url:
                        bucket_name = bucket
                        break
                
                # 해당 bucket의 모든 metric 확인 (디버깅용)
                metrics_found = set()
                for item in result_list[:10]:  # 처음 10개만 확인
                    if isinstance(item, dict) and item.get('metric'):
                        metrics_found.add(item.get('metric'))
                
                bucket_metrics_info.append({
                    'bucket': bucket_name,
                    'url': url[:60],
                    'total_items': len(result_list),
                    'metrics': list(metrics_found)
                })
                
                # metric 필터링으로 유효한 데이터 개수 확인
                valid_count = 0
                if feature_name in feature_metric_map:
                    expected_metric = feature_metric_map[feature_name]
                    for item in result_list:
                        if isinstance(item, dict):
                            item_metric = item.get('metric', '')
                            if item_metric == expected_metric:
                                # 취소 타입 추가 필터링
                                if feature_name in cancelled_type_map:
                                    item_cancelled_type = item.get('cancelledType', '')
                                    expected_types = cancelled_type_map[feature_name]
                                    if not any(expected_type in item_cancelled_type for expected_type in expected_types):
                                        if item_cancelled_type:
                                            continue
                                valid_count += 1
                
                # 가장 많은 유효한 데이터를 가진 응답 선택
                if valid_count > best_data_count:
                    best_data_count = valid_count
                    best_response = response
        
        # 디버깅 정보 출력
        if bucket_metrics_info:
            print(f"  [Debug] Available buckets and metrics:")
            for info in bucket_metrics_info:
                print(f"    - {info['bucket']}: {info['total_items']} items, metrics: {info['metrics']}")
        
        # 가장 좋은 응답 사용
        if best_response:
            api_data = best_response.get('data', {})
            print(f"  ✓ Selected best API response: {best_response.get('url', '')[:80]}... ({best_data_count} valid items)")
        elif reports_responses:
            # metric 필터링으로 데이터를 찾지 못한 경우
            if feature_name in feature_metric_map:
                expected_metric = feature_metric_map[feature_name]
                print(f"  ⚠ No response found with metric '{expected_metric}'")
                print(f"    Available metrics in buckets:")
                for info in bucket_metrics_info:
                    print(f"      - {info['bucket']}: {info['metrics']}")
            # 첫 번째 응답 사용 (나중에 필터링)
            api_data = reports_responses[0].get('data', {})
            print(f"  ⚠ Using first available response (will filter by metric): {reports_responses[0].get('url', '')[:80]}...")
        else:
            print("  ⚠ No API responses available")
            return chart_data
        
        # 필터링 통계 변수 초기화
        total_items = 0
        filtered_count = 0
        
        # 구조 5: {result: [...], resultMetric: ...} - 실제 확인된 구조
        if 'result' in api_data and isinstance(api_data.get('result'), list):
            result_list = api_data.get('result', [])
            print(f"    Found 'result' array with {len(result_list)} items")
            
            # 첫 번째 항목 구조 확인 (디버깅)
            if len(result_list) > 0:
                first_item = result_list[0]
                if isinstance(first_item, dict):
                    print(f"    First item keys: {list(first_item.keys())[:10]}")
                    print(f"    First item sample: {str(first_item)[:200]}")
            
            # 필터링 전 항목 수
            total_items = len(result_list)
            filtered_count = 0
            
            # result 배열의 각 항목 처리
            for i, item in enumerate(result_list):
                if isinstance(item, dict):
                    # metric 필드로 필터링 (체크박스 변경 시 API 요청이 발생하지 않으므로)
                    if feature_name in feature_metric_map:
                        expected_metric = feature_metric_map[feature_name]
                        item_metric = item.get('metric', '')
                        # metric이 일치하지 않으면 스킵
                        if item_metric != expected_metric:
                            filtered_count += 1
                            continue
                    
                    # 취소 타입 필터링 (취소 관련 피쳐인 경우)
                    # '취소'는 모든 취소 타입을 포함하므로 필터링하지 않음
                    if feature_name in cancelled_type_map:
                        item_cancelled_type = item.get('cancelledType', '')
                        expected_types = cancelled_type_map[feature_name]
                        # cancelledType이 예상된 타입 중 하나와 일치하는지 확인
                        if not any(expected_type in item_cancelled_type for expected_type in expected_types):
                            # cancelledType이 있고 예상과 다르면 스킵
                            if item_cancelled_type:
                                filtered_count += 1
                                continue
                    
                    # 날짜 필드 추출 (day_trend 필드 확인)
                    date_value = item.get('day_trend') or item.get('date') or item.get('dateLabel') or item.get('label') or item.get('day') or item.get('dateStr')
                    
                    # 값 필드 추출
                    value = item.get('value') or item.get('count') or item.get('data') or item.get('amount') or item.get('total') or item.get('bookingCount_sum')
                    
                    # 숫자 필드 찾기 (date가 아닌 숫자 필드)
                    if value is None:
                        for key, val in item.items():
                            if key not in ['date', 'dateLabel', 'label', 'day', 'feature', 'dateStr', 'day_trend', 'cancelledType', 'metric', 'bizItemId', 'bizItemName', 'bizItemOrder', 'bizItemRegDateTime'] and isinstance(val, (int, float)):
                                value = val
                                break
                    
                    chart_data.append({
                        "point_index": len(chart_data),  # 실제 추가된 인덱스 사용
                        "label": date_value,
                        "value": value,
                        "feature": feature_name or item.get('feature'),
                        "source": "api"
                    })
                elif isinstance(item, (int, float)):
                    # 단순 숫자 배열인 경우
                    chart_data.append({
                        "point_index": i,
                        "label": None,
                        "value": item,
                        "feature": feature_name,
                        "source": "api"
                    })
        
        # 구조 1: {dates: [...], data: [...], labels: [...]}
        elif 'dates' in api_data and 'data' in api_data:
            dates = api_data.get('dates', [])
            data_values = api_data.get('data', [])
            for i, (date, value) in enumerate(zip(dates, data_values)):
                chart_data.append({
                    "point_index": i,
                    "label": date,
                    "value": value,
                    "feature": feature_name,
                    "source": "api"
                })
        
        # 구조 2: {labels: [...], datasets: [{data: [...]}]}
        elif 'labels' in api_data and 'datasets' in api_data:
            labels = api_data.get('labels', [])
            datasets = api_data.get('datasets', [])
            if datasets and len(datasets) > 0:
                data_values = datasets[0].get('data', [])
                for i, (label, value) in enumerate(zip(labels, data_values)):
                    chart_data.append({
                        "point_index": i,
                        "label": label,
                        "value": value,
                        "feature": feature_name or datasets[0].get('label'),
                        "source": "api"
                    })
        
        # 구조 3: 배열 형태 [{date: ..., value: ...}, ...]
        elif isinstance(api_data, list):
            for i, item in enumerate(api_data):
                if isinstance(item, dict):
                    chart_data.append({
                        "point_index": i,
                        "label": item.get('date') or item.get('label') or item.get('dateLabel'),
                        "value": item.get('value') or item.get('count') or item.get('data'),
                        "feature": feature_name or item.get('feature'),
                        "source": "api"
                    })
        
        # 구조 4: 단순 배열 [value1, value2, ...]
        elif isinstance(api_data, list) and len(api_data) > 0 and not isinstance(api_data[0], dict):
            for i, value in enumerate(api_data):
                chart_data.append({
                    "point_index": i,
                    "label": None,
                    "value": value,
                    "feature": feature_name,
                    "source": "api"
                })
            
            if chart_data:
                print(f"  ✓ Extracted {len(chart_data)} data points from API")
                if len(chart_data) > 0:
                    print(f"    Sample: {chart_data[0]}")
                if filtered_count > 0:
                    print(f"    Filtered out {filtered_count} items (total: {total_items})")
            else:
                if 'result' in api_data and isinstance(api_data.get('result'), list):
                    result_list_for_debug = api_data.get('result', [])
                    if filtered_count > 0:
                        print(f"  ⚠ All {total_items} items were filtered out (filtered: {filtered_count})")
                        if feature_name in feature_metric_map:
                            expected_metric = feature_metric_map[feature_name]
                            print(f"    Feature '{feature_name}' expects metric: {expected_metric}")
                            # 실제 metric 값들 확인
                            actual_metrics = set()
                            for item in result_list_for_debug[:10]:  # 처음 10개만 확인
                                if isinstance(item, dict) and item.get('metric'):
                                    actual_metrics.add(item.get('metric'))
                            if actual_metrics:
                                print(f"    Actual metric values found: {list(actual_metrics)}")
                        if feature_name in cancelled_type_map:
                            print(f"    Feature '{feature_name}' expects cancelledType: {cancelled_type_map[feature_name]}")
                            # 실제 cancelledType 값들 확인
                            actual_types = set()
                            for item in result_list_for_debug[:10]:  # 처음 10개만 확인
                                if isinstance(item, dict) and item.get('cancelledType'):
                                    actual_types.add(item.get('cancelledType'))
                            if actual_types:
                                print(f"    Actual cancelledType values found: {list(actual_types)}")
                    else:
                        print(f"  ⚠ API response structure not recognized")
                else:
                    print(f"  ⚠ API response structure not recognized")
                if isinstance(api_data, dict):
                    print(f"    Keys: {list(api_data.keys())[:10]}")
                    # 첫 번째 값의 구조 확인
                    if api_data:
                        first_key = list(api_data.keys())[0]
                        first_value = api_data[first_key]
                        print(f"    First key '{first_key}' type: {type(first_value).__name__}")
                        if isinstance(first_value, (list, dict)) and len(str(first_value)) < 200:
                            print(f"    First value sample: {str(first_value)[:200]}")
                elif isinstance(api_data, list):
                    print(f"    Array length: {len(api_data)}")
                    if len(api_data) > 0:
                        print(f"    First item type: {type(api_data[0]).__name__}")
                        if isinstance(api_data[0], dict):
                            print(f"    First item keys: {list(api_data[0].keys())[:10]}")
                else:
                    print(f"    Type: {type(api_data).__name__}")
        
        return chart_data
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 데이터 스크래핑
        
        효율화: JS 방식으로 차트 데이터를 직접 추출 (place_hourly_inflow_graph.py 참조)
        JS 추출 실패 시에만 hover 방식을 fallback으로 사용
        """
        print("\n[Scraping] Starting booking trend chart scraping...")
        
        await self.setup_network_interception(page)
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        
        if not await self.wait_for_chart_load(page):
            print("  ⚠ Chart may not be fully loaded, continuing anyway...")
        
        # 모든 API 응답이 로드될 때까지 충분히 대기
        print("\n[Wait] Waiting for all API responses to be captured...")
        await asyncio.sleep(5)  # 추가 대기 시간
        
        # 캡처된 API 응답 수 확인
        reports_responses_count = len([
            r for r in self.network_responses 
            if '/reports' in r.get('url', '')
        ])
        print(f"  ✓ Captured {reports_responses_count} reports API responses")
        
        if reports_responses_count == 0:
            print("  ⚠ Warning: No reports API responses captured. Data extraction may fail.")
        else:
            # 각 응답의 bucket 정보 출력
            buckets_found = set()
            for response in self.network_responses:
                url = response.get('url', '')
                if '/reports' in url:
                    for bucket in ['day_trend', 'bookingCo', 'cancelled', 'price_sum']:
                        if bucket in url:
                            buckets_found.add(bucket)
                            break
            print(f"  ✓ Found buckets: {', '.join(buckets_found) if buckets_found else 'unknown'}")
        
        # 체크박스 피쳐 목록 가져오기
        features = await self.get_checkbox_features(page)
        
        if not features:
            print("  ⚠ No checkbox features found, extracting default chart data...")
            # API 방식 우선 시도
            api_data = await self.extract_chart_data_from_api(None, 0)
            js_data = {}
            hover_data = []
            
            if api_data and len(api_data) > 0:
                hover_data = api_data
                print(f"  ✓ Using data from API extraction ({len(hover_data)} points)")
            else:
                # JS 방식 시도
                js_data = await self.extract_chart_data_via_js(page)
                time_based_data = js_data.get("time_based_data", [])
                
                if time_based_data and len(time_based_data) > 0:
                    hover_data = time_based_data
                    print(f"  ✓ Using data from JS extraction ({len(hover_data)} points)")
                else:
                    hover_data = []
                    print("  ✗ Both API and JS extraction failed. No data collected.")
            
            result = {
                "url": self.stats_url,
                "scraped_at": datetime.now().isoformat(),
                "hover_data": hover_data,
                "js_data": js_data,
                "page_title": await page.title(),
            }
            return result
        
        # 모든 체크박스별로 데이터 수집
        # 중요: 체크박스 변경 시 새로운 API 요청이 발생하지 않으므로,
        # 이미 캡처된 모든 API 응답에서 각 피쳐의 데이터를 추출
        print("\n[Strategy] Extracting data from all captured API responses (no new requests on checkbox change)")
        
        all_feature_data = {}
        
        # 먼저 모든 API 응답에서 각 피쳐별 데이터를 한 번에 추출
        print("\n[Pre-extraction] Extracting data for all features from captured API responses...")
        for idx, feature_info in enumerate(features):
            feature_name = feature_info.get('feature', f'feature_{idx}')
            print(f"  [{idx + 1}/{len(features)}] Extracting data for: {feature_name}")
            
            # 모든 API 응답에서 해당 피쳐의 데이터 추출 (responses_before_count=0으로 설정하여 모든 응답 확인)
            api_data = await self.extract_chart_data_from_api(feature_name, 0)
            
            if api_data and len(api_data) > 0:
                print(f"    ✓ Found {len(api_data)} data points for {feature_name}")
                all_feature_data[feature_name] = {
                    "hover_data": api_data,
                    "js_data": {},
                    "api_data": api_data,
                    "data_source": "api"
                }
            else:
                print(f"    ⚠ No data found for {feature_name} in API responses")
                all_feature_data[feature_name] = {
                    "hover_data": [],
                    "js_data": {},
                    "api_data": [],
                    "data_source": "none"
                }
        
        # 체크박스 변경을 통한 차트 인스턴스 데이터 추출 (props.data에서 직접 추출)
        # 중요: 모든 체크박스를 해제하면 차트가 사라지므로, 현재 체크된 상태에서 props.data를 먼저 추출
        print("\n[Secondary] Extracting data from chart instances...")
        
        # 먼저 초기 상태(여러 피쳐가 체크된 상태)에서 props.data 추출
        print("  [Initial] Extracting props.data from initial state (multiple features checked)...")
        initial_js_data = await self.extract_props_data_simple(page)
        initial_time_based_data = initial_js_data.get("time_based_data", [])
        
        if initial_time_based_data:
            print(f"  ✓ Initial extraction: {len(initial_time_based_data)} data points")
            # 초기 데이터에서 각 피쳐별 데이터 분리
            for feature_name in all_feature_data.keys():
                filtered_data = [
                    item for item in initial_time_based_data
                    if item.get('feature_name') == feature_name or item.get('dataset_label') == feature_name
                ]
                if filtered_data:
                    existing_data = all_feature_data[feature_name].get("hover_data", [])
                    if not existing_data or len(filtered_data) > len(existing_data):
                        all_feature_data[feature_name]["hover_data"] = filtered_data
                        all_feature_data[feature_name]["js_data"] = initial_js_data
                        all_feature_data[feature_name]["data_source"] = "js_initial"
                        print(f"    ✓ {feature_name}: {len(filtered_data)} points from initial extraction")
        else:
            print("  ⚠ Initial extraction failed, trying individual checkbox method...")
        
        # API/초기 추출에서 데이터를 못 찾은 피쳐만 개별 처리
        print("\n[Individual] Processing features without data...")
        for idx, feature_info in enumerate(features):
            feature_name = feature_info.get('feature', f'feature_{idx}')
            
            existing_data = all_feature_data[feature_name].get("hover_data", [])
            if existing_data and len(existing_data) >= 1:
                print(f"  [{idx + 1}/{len(features)}] {feature_name}: 데이터 있음 ({len(existing_data)} points), 스킵")
                continue
            
            print(f"\n[Feature {idx + 1}/{len(features)}] Processing: {feature_name} (no data found)")
            
            # 모든 체크박스 해제하지 않고, 현재 피쳐만 체크 (다른 피쳐도 유지)
            # 체크박스 상태 변경: 현재 피쳐만 체크
            print(f"  [Check] Ensuring checkbox for {feature_name} is checked...")
            checkbox_checked = await self.ensure_checkbox_checked(page, idx)
            if not checkbox_checked:
                print(f"  ⚠ Failed to check checkbox, skipping {feature_name}")
                continue
            
            # props.data가 업데이트될 때까지 대기
            print(f"  [Wait] Waiting for props.data update...")
            await asyncio.sleep(2)  # 초기 대기
            
            # props.data 업데이트 확인 (최대 5초)
            chart_updated = False
            for attempt in range(10):
                await asyncio.sleep(0.5)
                
                props_data_check = await page.evaluate(
                    """
                    () => {
                        const canvas = document.querySelector('[class*="chart-wrap"] canvas') ||
                                      document.querySelector('.panel-body canvas') ||
                                      document.querySelector('canvas');
                        if (!canvas) return { found: false, error: 'canvas not found' };
                        
                        const fiberKey = Object.keys(canvas).find(k => k.startsWith('__reactFiber'));
                        if (!fiberKey) return { found: false, error: 'fiber not found' };
                        
                        let fiber = canvas[fiberKey];
                        let depth = 0;
                        
                        while (fiber && depth < 30) {
                            if (fiber.memoizedProps && fiber.memoizedProps.data && Array.isArray(fiber.memoizedProps.data)) {
                                const data = fiber.memoizedProps.data;
                                if (data.length > 0 && Array.isArray(data[0]) && typeof data[0][0] === 'string') {
                                    return {
                                        found: true,
                                        seriesCount: data.length,
                                        firstSeriesFeature: data[0][0],
                                        firstSeriesLength: data[0].length,
                                        labelsLength: fiber.memoizedProps.label?.length || 0
                                    };
                                }
                            }
                            fiber = fiber.return;
                            depth++;
                        }
                        return { found: false, depth: depth };
                    }
                    """
                )
                
                if props_data_check.get('found'):
                    chart_updated = True
                    print(f"    ✓ props.data 업데이트 확인 (시리즈: {props_data_check.get('seriesCount')}, 첫 피쳐: {props_data_check.get('firstSeriesFeature')})")
                    break
            
            if not chart_updated:
                print(f"    ⚠ props.data 업데이트를 확인하지 못했지만 계속 진행...")
            
            # 간단한 props.data 추출 방식 사용 (복잡한 JS 방식 대신)
            print(f"  [Method] Extracting data from props.data (simple)...")
            js_data = await self.extract_props_data_simple(page)
            time_based_data = js_data.get("time_based_data", [])
            
            if time_based_data and len(time_based_data) > 0:
                # 현재 피쳐와 일치하는 데이터만 필터링
                filtered_data = [
                    item for item in time_based_data
                    if item.get('feature_name') == feature_name or item.get('dataset_label') == feature_name
                ]
                
                if filtered_data:
                    print(f"  ✓ Found {len(filtered_data)} data points for {feature_name} via JS extraction")
                    # 기존 데이터가 없거나 더 많은 데이터를 찾은 경우 업데이트
                    existing_data = all_feature_data[feature_name].get("hover_data", [])
                    if not existing_data or len(filtered_data) > len(existing_data):
                        all_feature_data[feature_name]["hover_data"] = filtered_data
                        all_feature_data[feature_name]["js_data"] = js_data
                        all_feature_data[feature_name]["data_source"] = "js"
                    else:
                        print(f"    (기존 API 데이터 유지: {len(existing_data)} points)")
                elif time_based_data:
                    # 필터링 결과가 없으면 모든 데이터 사용 (현재 활성화된 피쳐의 데이터)
                    print(f"  ✓ Found {len(time_based_data)} data points (using all data) for {feature_name}")
                    existing_data = all_feature_data[feature_name].get("hover_data", [])
                    if not existing_data or len(time_based_data) > len(existing_data):
                        all_feature_data[feature_name]["hover_data"] = time_based_data
                        all_feature_data[feature_name]["js_data"] = js_data
                        all_feature_data[feature_name]["data_source"] = "js"
                    else:
                        print(f"    (기존 API 데이터 유지: {len(existing_data)} points)")
                else:
                    print(f"  ⚠ No matching data found for {feature_name}")
            else:
                print(f"  ⚠ JS extraction failed for {feature_name}")
        
        # 날짜 범위 계산
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        
        # 모든 피쳐 데이터에서 최대 데이터 포인트 수 확인
        max_points = max(
            len(feat_data.get("hover_data", [])) 
            for feat_data in all_feature_data.values()
        ) if all_feature_data else 0
        
        # 데이터가 없으면 기본값 설정
        if max_points == 0:
            max_points = 15  # 기본 15일 데이터
            print(f"  ⚠ No data found for any feature, using default {max_points} points")
        
        print(f"\n[Data Summary]")
        print(f"  Total features: {len(all_feature_data)}")
        print(f"  Max data points: {max_points}")
        for feature_name, feat_data in all_feature_data.items():
            hover_data = feat_data.get("hover_data", [])
            data_source = feat_data.get("data_source", "unknown")
            print(f"    - {feature_name}: {len(hover_data)} points ({data_source})")
        
        # 날짜별로 데이터 결합
        combined_data = []
        for point_idx in range(max_points):
            # 날짜 계산: 최신 날짜(start_date)에서 역순으로
            date_offset = max_points - 1 - point_idx  # 역순 인덱스
            row_date = start_dt - timedelta(days=date_offset)
            date_str = row_date.strftime("%Y-%m-%d")
            
            row_data = {
                "date": date_str,
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
                    # 데이터가 없는 경우 0으로 채우기 (None 대신)
                    row_data[f"{feature_name}_value"] = 0
                    row_data[f"{feature_name}_label"] = date_str
                    row_data[f"{feature_name}_tooltip"] = f"{feature_name}: 0"
            
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

