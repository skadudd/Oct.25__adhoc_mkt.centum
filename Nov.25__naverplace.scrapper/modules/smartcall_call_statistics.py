#!/usr/bin/env python3
"""
네이버 스마트플레이스 스마트콜 통화 통계 데이터 스크래퍼 모듈
"""

import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import Page
from .base_scraper import BaseScraper


class SmartcallCallStatisticsScraper(BaseScraper):
    """스마트콜 통화 통계 데이터 스크래퍼"""
    
    def __init__(self, username: str, password: str, start_date: str = "2025-12-09", end_date: str = "2025-12-15", output_base_dir: str = "data/naverplace"):
        super().__init__(username, password, start_date, end_date, output_base_dir)
        # URL 동적 생성
        self.stats_url = (
            f"https://smartcall.smartplace.naver.com/statistics/1191881927"
            f"?startDate={start_date}&endDate={end_date}&bookingBusinessId=603738"
        )
    
    def get_module_name(self) -> str:
        return "smartcall_call_statistics"
    
    async def click_daily_tab(self, page: Page) -> bool:
        """일별 통화 탭 클릭"""
        print("\n[Tab] Clicking daily call tab...")
        try:
            # 일별 통화 탭 선택자
            daily_tab_selector = "#__next > div > div:nth-child(3) > div > div.call_section > div.styles_call_info__qa5Bn > div.styles_info_tab__E4QqY > ul > li:nth-child(2) > a"
            
            # 탭이 나타날 때까지 대기
            await page.wait_for_selector(daily_tab_selector, timeout=10000)
            await asyncio.sleep(1)
            
            # 탭 클릭
            await page.click(daily_tab_selector)
            await asyncio.sleep(2)  # 탭 전환 대기
            
            print("  ✓ Daily call tab clicked")
            return True
        except Exception as e:
            print(f"  ⚠ Error clicking daily tab: {e}")
            # 대체 선택자 시도
            try:
                # 더 간단한 선택자로 시도
                tabs = await page.query_selector_all("div.styles_info_tab__E4QqY ul li a")
                if len(tabs) >= 2:
                    await tabs[1].click()
                    await asyncio.sleep(2)
                    print("  ✓ Daily call tab clicked (alternative method)")
                    return True
            except Exception:
                pass
            return False
    
    async def extract_table_data(self, page: Page) -> list:
        """통화 통계 테이블 데이터 추출"""
        print("\n[Data Extraction] Extracting call statistics table data...")
        
        table_data = []
        
        try:
            # 테이블 선택자 (task.md에 명시된 정확한 selector 사용)
            table_selector = "#call-daily > div > div.styles_table_scroll__or3Yy > table"
            
            await page.wait_for_selector(table_selector, timeout=15000)
            await asyncio.sleep(5)  # 테이블 로딩 대기 (더 긴 대기 시간)
            
            # 테이블 구조 디버깅 (wait_for_function 전에)
            table_structure = await page.evaluate(
                """
                () => {
                    const table = document.querySelector('#call-daily > div > div.styles_table_scroll__or3Yy > table');
                    if (!table) {
                        return { error: 'Table not found' };
                    }
                    
                    const thead = table.querySelector('thead');
                    const tbody = table.querySelector('tbody');
                    const allTrs = table.querySelectorAll('tr');
                    
                    return {
                        hasThead: !!thead,
                        hasTbody: !!tbody,
                        totalTrs: allTrs.length,
                        theadTrCount: thead ? thead.querySelectorAll('tr').length : 0,
                        tbodyTrCount: tbody ? tbody.querySelectorAll('tr').length : 0,
                        firstTrCells: allTrs.length > 0 ? allTrs[0].querySelectorAll('th, td').length : 0
                    };
                }
                """
            )
            print(f"  [Table Structure] {table_structure}")
            
            # 테이블이 완전히 로드될 때까지 대기 (조건 완화)
            try:
                await page.wait_for_function(
                    "() => { const table = document.querySelector('#call-daily > div > div.styles_table_scroll__or3Yy > table'); return table !== null; }",
                    timeout=5000
                )
            except Exception as e:
                print(f"  ⚠ wait_for_function timeout: {e}")
            
            await asyncio.sleep(3)  # 추가 대기
            
            # 테이블 구조 디버깅
            table_structure = await page.evaluate(
                """
                () => {
                    const table = document.querySelector('#call-daily > div > div.styles_table_scroll__or3Yy > table');
                    if (!table) {
                        return { error: 'Table not found' };
                    }
                    
                    const thead = table.querySelector('thead');
                    const tbody = table.querySelector('tbody');
                    const allTrs = table.querySelectorAll('tr');
                    
                    return {
                        hasThead: !!thead,
                        hasTbody: !!tbody,
                        totalTrs: allTrs.length,
                        theadTrCount: thead ? thead.querySelectorAll('tr').length : 0,
                        tbodyTrCount: tbody ? tbody.querySelectorAll('tr').length : 0,
                        firstTrCells: allTrs.length > 0 ? allTrs[0].querySelectorAll('th, td').length : 0
                    };
                }
                """
            )
            print(f"  [Table Structure] {table_structure}")
            
            # JavaScript로 테이블 데이터 추출 (인덱스 열 + 데이터 열 합치기)
            js_result = await page.evaluate(
                """
                () => {
                    const result = {
                        headers: [],
                        rows: [],
                        indexRows: [],
                        dataRows: [],
                        debug: {}
                    };
                    
                    // 1. 인덱스 열 추출 (고정된 테이블)
                    const fixedTable = document.querySelector('#call-daily > div > div.styles_table_fixed__L7rWc');
                    result.debug.fixedTableFound = !!fixedTable;
                    
                    if (fixedTable) {
                        const fixedTableEl = fixedTable.querySelector('table');
                        result.debug.fixedTableElFound = !!fixedTableEl;
                        
                        if (fixedTableEl) {
                            const fixedThead = fixedTableEl.querySelector('thead');
                            result.debug.fixedTheadFound = !!fixedThead;
                            
                            if (fixedThead) {
                                const fixedTrs = fixedThead.querySelectorAll('tr');
                                result.debug.fixedTrsCount = fixedTrs.length;
                                
                                if (fixedTrs.length > 0) {
                                    // 인덱스 열의 헤더 추출 (첫 번째 tr에서)
                                    const firstTr = fixedTrs[0];
                                    let indexHeaderCells = firstTr.querySelectorAll('th');
                                    if (indexHeaderCells.length === 0) {
                                        indexHeaderCells = firstTr.querySelectorAll('td');
                                    }
                                    const indexHeaders = Array.from(indexHeaderCells).map(cell => {
                                        return (cell.innerText || cell.textContent || '').trim();
                                    });
                                    
                                    // 데이터 열의 헤더 추출 (마지막 tr에서)
                                    const lastTr = fixedTrs[fixedTrs.length - 1];
                                    let dataHeaderCells = lastTr.querySelectorAll('th');
                                    if (dataHeaderCells.length === 0) {
                                        dataHeaderCells = lastTr.querySelectorAll('td');
                                    }
                                    const dataHeaders = Array.from(dataHeaderCells).map(cell => {
                                        return (cell.innerText || cell.textContent || '').trim();
                                    });
                                    
                                    // 헤더 합치기: 인덱스 헤더 + 데이터 헤더
                                    result.headers = [...indexHeaders, ...dataHeaders];
                                    result.debug.indexHeaders = indexHeaders;
                                    result.debug.dataHeaders = dataHeaders;
                                    result.debug.headersExtracted = result.headers.length;
                                    
                                    // 인덱스 열의 모든 데이터 행 추출
                                    // 헤더는 첫 번째 tr만 (TR[0]), 데이터는 TR[1]부터
                                    const headerRowCount = 1;
                                    result.debug.headerRowCount = headerRowCount;
                                    
                                    // 디버깅: 각 tr의 구조 확인
                                    for (let i = 0; i < fixedTrs.length; i++) {
                                        const tr = fixedTrs[i];
                                        const tds = tr.querySelectorAll('td');
                                        const ths = tr.querySelectorAll('th');
                                        result.debug[`tr${i}_tds`] = tds.length;
                                        result.debug[`tr${i}_ths`] = ths.length;
                                    }
                                    
                                    // TR[1]부터 모든 데이터 행 추출 (헤더 제외)
                                    for (let i = headerRowCount; i < fixedTrs.length; i++) {
                                        const tr = fixedTrs[i];
                                        // td와 th 모두 확인 (인덱스 열은 th일 수도 있음)
                                        let cells = tr.querySelectorAll('td');
                                        if (cells.length === 0) {
                                            cells = tr.querySelectorAll('th');
                                        }
                                        
                                        if (cells.length > 0) {
                                            const row = Array.from(cells).map(cell => {
                                                return (cell.innerText || cell.textContent || '').trim();
                                            });
                                            result.indexRows.push(row);
                                            result.debug[`indexRow${i}`] = row;
                                        } else {
                                            result.debug[`indexRow${i}_empty`] = true;
                                        }
                                    }
                                    
                                    result.debug.indexRowsExtracted = result.indexRows.length;
                                    result.debug.indexRowIndices = Array.from({length: result.indexRows.length}, (_, idx) => headerRowCount + idx);
                                }
                            }
                        }
                    }
                    
                    // 2. 데이터 열 추출 (스크롤 가능한 테이블)
                    const scrollTable = document.querySelector('#call-daily > div > div.styles_table_scroll__or3Yy > table');
                    if (!scrollTable) {
                        console.log('Scroll table not found');
                        result.debug.error = 'Scroll table not found';
                        return result;
                    }
                    
                    result.debug.tableFound = true;
                    
                    // 데이터 열의 헤더 추출 (인덱스 열에서 헤더를 가져오지 못한 경우에만)
                    if (result.headers.length === 0) {
                        const thead = scrollTable.querySelector('thead');
                        if (thead) {
                            const headerTrs = thead.querySelectorAll('tr');
                            if (headerTrs.length > 0) {
                                const lastTr = headerTrs[headerTrs.length - 1];
                                let headerCells = lastTr.querySelectorAll('th');
                                if (headerCells.length === 0) {
                                    headerCells = lastTr.querySelectorAll('td');
                                }
                                result.headers = Array.from(headerCells).map(cell => {
                                    return (cell.innerText || cell.textContent || '').trim();
                                });
                            }
                        }
                    }
                    
                    // 데이터 열의 행 데이터 추출
                    const tbody = scrollTable.querySelector('tbody');
                    const thead = scrollTable.querySelector('thead');
                    
                    result.debug.scrollTbodyFound = !!tbody;
                    result.debug.scrollTheadFound = !!thead;
                    
                    if (tbody) {
                        const trs = tbody.querySelectorAll('tr');
                        result.debug.scrollTbodyTrsCount = trs.length;
                        for (let tr of trs) {
                            const tds = tr.querySelectorAll('td');
                            if (tds.length > 0) {
                                const row = Array.from(tds).map(td => {
                                    return (td.innerText || td.textContent || '').trim();
                                });
                                if (row.length > 0 && row.some(cell => cell)) {
                                    result.dataRows.push(row);
                                }
                            }
                        }
                    } else if (thead) {
                        const headerTrs = thead.querySelectorAll('tr');
                        result.debug.scrollTheadTrsCount = headerTrs.length;
                        // 헤더는 첫 번째 tr만 (TR[0]), 데이터는 TR[1]부터
                        const headerRowCount = 1;
                        result.debug.scrollHeaderRowCount = headerRowCount;
                        
                        // TR[1]부터 모든 데이터 행 추출 (헤더 제외)
                        for (let i = headerRowCount; i < headerTrs.length; i++) {
                            const tr = headerTrs[i];
                            const tds = tr.querySelectorAll('td');
                            if (tds.length > 0) {
                                const row = Array.from(tds).map(td => {
                                    return (td.innerText || td.textContent || '').trim();
                                });
                                if (row.length > 0 && row.some(cell => cell)) {
                                    result.dataRows.push(row);
                                    result.debug[`dataRow${i}`] = row;
                                }
                            }
                        }
                    } else {
                        // tbody와 thead 모두 없는 경우: table 하위의 모든 tr 확인
                        const allTrs = scrollTable.querySelectorAll('tr');
                        result.debug.scrollAllTrsCount = allTrs.length;
                        // 헤더는 첫 번째 tr만 (TR[0]), 데이터는 TR[1]부터
                        const headerRowCount = 1;
                        for (let i = headerRowCount; i < allTrs.length; i++) {
                            const tr = allTrs[i];
                            const tds = tr.querySelectorAll('td');
                            if (tds.length > 0) {
                                const row = Array.from(tds).map(td => {
                                    return (td.innerText || td.textContent || '').trim();
                                });
                                if (row.length > 0 && row.some(cell => cell)) {
                                    result.dataRows.push(row);
                                    result.debug[`dataRow${i}`] = row;
                                }
                            }
                        }
                    }
                    
                    result.debug.dataRowsExtracted = result.dataRows.length;
                    
                    // 3. 인덱스 열과 데이터 열 합치기
                    console.log('Index rows:', result.indexRows.length, 'Data rows:', result.dataRows.length);
                    
                    // 행 수가 같은지 확인하고 합치기
                    const maxRows = Math.max(result.indexRows.length, result.dataRows.length);
                    for (let i = 0; i < maxRows; i++) {
                        const indexRow = result.indexRows[i] || [];
                        const dataRow = result.dataRows[i] || [];
                        
                        // 인덱스 열의 첫 번째 셀을 키로 사용하고, 나머지와 데이터 열을 합치기
                        const combinedRow = [...indexRow, ...dataRow];
                        if (combinedRow.length > 0 && combinedRow.some(cell => cell)) {
                            result.rows.push(combinedRow);
                        }
                    }
                    
                    console.log('Final combined rows count:', result.rows.length);
                    
                    return result;
                }
                """
            )
            
            print(f"  JavaScript result: headers={len(js_result.get('headers', []))}, rows={len(js_result.get('rows', []))}")
            print(f"    Index rows: {len(js_result.get('indexRows', []))}, Data rows: {len(js_result.get('dataRows', []))}")
            if js_result.get('debug'):
                debug_info = js_result.get('debug', {})
                print(f"  Debug info:")
                print(f"    Fixed table found: {debug_info.get('fixedTableFound', 'N/A')}")
                print(f"    Fixed table element found: {debug_info.get('fixedTableElFound', 'N/A')}")
                print(f"    Fixed thead found: {debug_info.get('fixedTheadFound', 'N/A')}")
                print(f"    Fixed TRs count: {debug_info.get('fixedTrsCount', 'N/A')}")
                print(f"    Headers extracted: {debug_info.get('headersExtracted', 'N/A')}")
                print(f"    Header row count: {debug_info.get('headerRowCount', 'N/A')}")
                print(f"    Index rows extracted: {debug_info.get('indexRowsExtracted', 'N/A')}")
                print(f"    Scroll tbody found: {debug_info.get('scrollTbodyFound', 'N/A')}")
                print(f"    Scroll thead found: {debug_info.get('scrollTheadFound', 'N/A')}")
                print(f"    Scroll thead TRs count: {debug_info.get('scrollTheadTrsCount', 'N/A')}")
                print(f"    Scroll header row count: {debug_info.get('scrollHeaderRowCount', 'N/A')}")
                print(f"    Data rows extracted: {debug_info.get('dataRowsExtracted', 'N/A')}")
                
                # 각 tr의 구조 확인
                for i in range(8):
                    td_key = f'tr{i}_tds'
                    th_key = f'tr{i}_ths'
                    if td_key in debug_info or th_key in debug_info:
                        print(f"    TR[{i}]: TDs={debug_info.get(td_key, 0)}, THs={debug_info.get(th_key, 0)}")
                
                # 인덱스 행 샘플
                for i in range(2, 8):
                    row_key = f'indexRow{i}'
                    empty_key = f'indexRow{i}_empty'
                    if row_key in debug_info:
                        print(f"    Index row[{i}]: {debug_info[row_key]}")
                    elif empty_key in debug_info:
                        print(f"    Index row[{i}]: EMPTY")
                
                # 데이터 행 샘플
                for i in range(2, 8):
                    row_key = f'dataRow{i}'
                    if row_key in debug_info:
                        print(f"    Data row[{i}]: {debug_info[row_key]}")
            
            # 인덱스 행 샘플 출력
            if js_result.get('indexRows'):
                print(f"    Index rows sample (first 3):")
                for i, idx_row in enumerate(js_result.get('indexRows', [])[:3], 1):
                    print(f"      {i}. {idx_row}")
            else:
                print(f"    ⚠ No index rows extracted!")
            
            if js_result.get('headers') and js_result.get('rows'):
                headers = js_result['headers']
                rows = js_result['rows']
                
                print(f"  ✓ Found table with {len(headers)} columns and {len(rows)} rows")
                print(f"    Headers: {headers}")
                
                # 딕셔너리 형태로 변환
                for row in rows:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                    table_data.append(row_dict)
                
                print(f"  ✓ Extracted {len(table_data)} rows")
                if len(table_data) > 0:
                    print(f"    Sample row: {table_data[0]}")
                    for i, item in enumerate(table_data[:3], 1):
                        print(f"    {i}. {item}")
                else:
                    print(f"    ⚠ Warning: table_data is empty after conversion")
            else:
                print("  ⚠ No table data found via JavaScript")
                
                # BeautifulSoup으로 재시도 (인덱스 열 + 데이터 열 합치기)
                print("  Trying BeautifulSoup...")
                soup = BeautifulSoup(await page.content(), 'html.parser')
                
                # 1. 인덱스 열 추출
                fixed_table = soup.select_one('#call-daily > div > div.styles_table_fixed__L7rWc table')
                index_rows = []
                headers = []
                
                if fixed_table:
                    fixed_thead = fixed_table.find('thead')
                    if fixed_thead:
                        fixed_header_trs = fixed_thead.find_all('tr')
                        if fixed_header_trs:
                            # 마지막 tr에서 헤더 추출
                            last_tr = fixed_header_trs[-1]
                            ths = last_tr.find_all('th')
                            if not ths:
                                ths = last_tr.find_all('td')
                            headers = [th.get_text(strip=True) for th in ths]
                        
                        # 인덱스 열의 데이터 행 추출
                        header_row_count = min(2, len(fixed_header_trs)) if fixed_header_trs else 0
                        for tr in fixed_header_trs[header_row_count:]:
                            tds = tr.find_all('td')
                            if tds:
                                row_data = [td.get_text(strip=True) for td in tds]
                                index_rows.append(row_data)
                
                # 2. 데이터 열 추출
                scroll_table = soup.select_one('#call-daily > div > div.styles_table_scroll__or3Yy > table')
                data_rows = []
                
                if scroll_table:
                    # 헤더가 없으면 데이터 열에서 추출
                    if not headers:
                        scroll_thead = scroll_table.find('thead')
                        if scroll_thead:
                            scroll_header_trs = scroll_thead.find_all('tr')
                            if scroll_header_trs:
                                last_tr = scroll_header_trs[-1]
                                ths = last_tr.find_all('th')
                                if not ths:
                                    ths = last_tr.find_all('td')
                                headers = [th.get_text(strip=True) for th in ths]
                    
                    # 데이터 행 추출
                    scroll_tbody = scroll_table.find('tbody')
                    scroll_thead = scroll_table.find('thead')
                    
                    if scroll_tbody:
                        trs = scroll_tbody.find_all('tr')
                        for tr in trs:
                            tds = tr.find_all('td')
                            if tds:
                                row_data = [td.get_text(strip=True) for td in tds]
                                data_rows.append(row_data)
                    elif scroll_thead:
                        header_trs = scroll_thead.find_all('tr')
                        header_row_count = min(2, len(header_trs)) if header_trs else 0
                        for tr in header_trs[header_row_count:]:
                            tds = tr.find_all('td')
                            if tds:
                                row_data = [td.get_text(strip=True) for td in tds]
                                data_rows.append(row_data)
                
                # 3. 인덱스 열과 데이터 열 합치기
                max_rows = max(len(index_rows), len(data_rows))
                for i in range(max_rows):
                    index_row = index_rows[i] if i < len(index_rows) else []
                    data_row = data_rows[i] if i < len(data_rows) else []
                    combined_row = index_row + data_row
                    
                    if combined_row:
                        row_dict = {}
                        for j, header in enumerate(headers):
                            if j < len(combined_row):
                                row_dict[header] = combined_row[j]
                        table_data.append(row_dict)
                
                print(f"  ✓ Extracted {len(table_data)} rows via BeautifulSoup (combined {len(index_rows)} index rows + {len(data_rows)} data rows)")
            
            return table_data
            
        except Exception as e:
            print(f"  ✗ Error extracting table data: {e}")
            import traceback
            traceback.print_exc()
            return table_data
    
    async def scrape(self, page: Page) -> dict:
        """통계 페이지에서 통화 통계 데이터 스크래핑"""
        print("\n[Scraping] Starting smartcall call statistics scraping...")
        
        print(f"  Navigating to: {self.stats_url}")
        await page.goto(self.stats_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 페이지 로딩 대기
        
        # 일별 통화 탭 클릭
        await self.click_daily_tab(page)
        
        # 테이블 데이터 추출
        table_data = await self.extract_table_data(page)
        
        print(f"\n[Scrape Result] table_data type: {type(table_data)}, length: {len(table_data) if isinstance(table_data, list) else 'N/A'}")
        if isinstance(table_data, list) and len(table_data) > 0:
            print(f"  First row: {table_data[0]}")
        
        result = {
            "url": self.stats_url,
            "scraped_at": datetime.now().isoformat(),
            "call_statistics_data": table_data,
            "page_title": await page.title(),
        }
        
        return result

