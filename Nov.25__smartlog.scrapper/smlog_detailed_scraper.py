#!/usr/bin/env python3
"""
SMLOG Detailed Data Scraper
Extracts data from each page (네트워크, 키워드, 사이트, 미디어)
Sets same date for start and end, iterates from 2025.8.18
Exports data as CSV/Excel files with page names
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os


class SMLogDetailedScraper:
    def __init__(self, username, password, svid="33138", start_date=None, days_limit=None):
        self.username = username
        self.password = password
        self.svid = svid
        self.base_url = "https://smlog.co.kr"
        self.login_url = f"{self.base_url}/2020/member/login.html"
        self.stats_url = f"{self.base_url}/hmisNew/ad_statistics.html?svid={svid}"

        # Buttons to scrape
        self.buttons_to_scrape = ["네트워크", "키워드", "사이트", "미디어"]

        # Start date (default: 2025-08-18)
        self.start_date = start_date if start_date else datetime(2025, 11, 5)

        # Limit number of days to scrape (default: None = all days)
        self.days_limit = days_limit

    async def login_and_navigate(self, page):
        """Complete login and navigation flow"""
        print("\n[Navigation] Starting login and navigation flow...")

        # Step 1: Login page
        print("  [1/5] Navigating to login page...")
        await page.goto(self.login_url, wait_until="networkidle")
        await asyncio.sleep(1)

        # Step 2: Enter credentials
        print("  [2/5] Entering credentials...")
        await page.fill('#id', self.username)
        await page.fill('input[type="password"]', self.password)

        # Step 3: Click login button
        print("  [3/5] Clicking login button...")
        login_button = await page.query_selector('.login-button-01')
        if login_button:
            await login_button.click()
            await asyncio.sleep(1)

        # Step 4: Click HMIS button
        print("  [4/5] Clicking HMIS button...")
        hmis_button = await page.query_selector('.hmis')
        if hmis_button:
            await hmis_button.click()
            await asyncio.sleep(1)

        # Step 5: Click service domain link
        print("  [5/5] Clicking service domain link...")
        service_links = await page.query_selector_all('.service-domain-url')
        for link in service_links:
            href = await link.get_attribute('href')
            if href and f"svid={self.svid}" in href:
                await link.click()
                await asyncio.sleep(1)
                break

        # Navigate to statistics page
        await page.goto(self.stats_url, wait_until="domcontentloaded")
        await asyncio.sleep(1)

        print("✓ Navigation completed successfully")
        return True

    async def find_and_click_button(self, page, button_text):
        """Find and click a button by text"""
        print(f"\n[Button] Looking for button: {button_text}")

        try:
            # Try to find the page-tab element directly
            tabs = await page.query_selector_all('div.page-tab')
            print(f"  Found {len(tabs)} page tabs")

            for tab in tabs:
                text = await tab.inner_text()
                print(f"    Tab text: '{text}'")
                if text == button_text or button_text in text:
                    print(f"  ✓ Found matching tab: '{text}'")
                    await tab.click()
                    await asyncio.sleep(1)
                    print(f"  ✓ Button clicked")
                    return True

            print(f"  ✗ Button not found in {len(tabs)} tabs")
            return False

        except Exception as e:
            print(f"  ✗ Error finding button: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def find_date_picker(self, page):
        """Find the date picker elements"""
        print(f"\n[DatePicker] Looking for date picker...")

        try:
            # Look for date picker input fields
            date_inputs = await page.query_selector_all('input[type="date"], input[placeholder*="date"], input[class*="date"]')
            print(f"  Found {len(date_inputs)} potential date input fields")

            # Also look for calendar elements
            calendar_cells = await page.query_selector_all('td[class*="weekend"][class*="active"][class*="available"], td[class*="start-date"], td[class*="end-date"]')
            print(f"  Found {len(calendar_cells)} calendar cells")

            return date_inputs, calendar_cells

        except Exception as e:
            print(f"  Error finding date picker: {e}")
            return [], []

    async def set_date_range(self, page, target_date):
        """Set same date for both start and end using the on-page controls (no JS injection)."""
        print(f"\n[Date] Setting date to {target_date.strftime('%Y-%m-%d')}")

        try:
            date_format_kr = target_date.strftime('%Y.%m.%d')
            date_range_str = f"{date_format_kr} - {date_format_kr}"

            # 1) Focus the date input
            try:
                daterange_input = await page.wait_for_selector('input[name="daterange"]', timeout=5000)
            except Exception:
                print("  ✗ daterange input not found")
                return False

            await daterange_input.click()
            await asyncio.sleep(0.3)

            # 2) Clear existing text using keyboard shortcuts (Mac & Win)
            cleared = False
            for shortcut in ['Meta+A', 'Control+A']:
                try:
                    await daterange_input.press(shortcut)
                    await daterange_input.press('Backspace')
                    cleared = True
                    break
                except Exception:
                    continue

            if not cleared:
                await daterange_input.fill('')

            await asyncio.sleep(0.2)

            # 3) Type the new date range
            await daterange_input.type(date_range_str, delay=40)
            print(f"  Filled daterange: {date_range_str}")
            await asyncio.sleep(0.5)

            # Blur the input to ensure changes are registered
            for key in ['Tab', 'Enter']:
                try:
                    await daterange_input.press(key)
                    await asyncio.sleep(0.2)
                    break
                except Exception:
                    continue

            # 4) Click the "적용" (Apply) button
            apply_button = None
            apply_selectors = [
                'button.applyBtn',
                '.applyBtn',
                'button.btn-primary.applyBtn',
                'button[class*="applyBtn"]'
            ]

            for selector in apply_selectors:
                try:
                    candidate = await page.wait_for_selector(selector, timeout=2000)
                    if candidate and await candidate.is_visible():
                        apply_button = candidate
                        print(f"  Found apply button with selector: {selector}")
                        break
                except Exception:
                    continue

            if apply_button:
                print("  Clicking apply button...")
                await apply_button.click()
                await asyncio.sleep(1.5)
                print("  ✓ Apply button clicked")
            else:
                print("  ℹ Apply button not visible; continuing")

            # 5) Click the "조회하기" (Search) button
            search_button = None
            search_selectors = [
                '#search_btn',
                '.btn-container-search',
                'div.btn-container-search',
                '[id="search_btn"]'
            ]

            for selector in search_selectors:
                try:
                    candidate = await page.wait_for_selector(selector, timeout=3000)
                    if candidate:
                        search_button = candidate
                        print(f"  Found search button with selector: {selector}")
                        break
                except Exception:
                    continue

            if search_button:
                print("  Clicking search button...")
                await search_button.click()
                await asyncio.sleep(2)
                print("  ✓ Search button clicked")
            else:
                print("  ⚠ Search button not found; data may not refresh")

            # 6) Verify the input reflects our target date (retry up to 3 times)
            date_set_correctly = False
            for verify_attempt in range(3):
                current_value = await daterange_input.input_value()
                print(f"  Verification attempt {verify_attempt + 1}: {current_value}")
                if current_value.strip() == date_range_str:
                    print("  ✓ Date confirmed on input")
                    date_set_correctly = True
                    break

                # Retry by re-entering the date
                print("  ⚠ Date mismatch, re-entering value")
                await daterange_input.click()
                for shortcut in ['Meta+A', 'Control+A']:
                    try:
                        await daterange_input.press(shortcut)
                        await daterange_input.press('Backspace')
                        break
                    except Exception:
                        continue
                await daterange_input.fill('')
                await asyncio.sleep(0.2)
                await daterange_input.type(date_range_str, delay=40)
                await asyncio.sleep(0.3)
                try:
                    await daterange_input.press('Tab')
                except Exception:
                    pass
                await asyncio.sleep(0.3)
                if apply_button:
                    await apply_button.click()
                    await asyncio.sleep(1)
                if search_button:
                    await search_button.click()
                    await asyncio.sleep(2)

            if not date_set_correctly:
                print(f"  ⚠ Unable to confirm date value (expected {date_range_str})")

            return True

        except Exception as e:
            print(f"  Error setting date: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def extract_table_data(self, page):
        """Extract table data from card-table"""
        print(f"\n[Table] Extracting table data...")

        try:
            # Wait for table to load - check if table exists and has data
            max_retries = 3
            for retry in range(max_retries):
                await asyncio.sleep(2)  # Wait for page to load
                
                soup = BeautifulSoup(await page.content(), 'html.parser')

                # Find the card-table
                card_table = soup.find('table', class_=lambda x: x and ('card-table' in str(x).lower() or 'table-centered' in str(x)))

                if not card_table:
                    # Try alternative selectors
                    card_table = soup.find('table', class_='table')
                
                if not card_table:
                    # Try finding any table
                    card_table = soup.find('table')

                if card_table:
                    # Check if table has data rows
                    tbody = card_table.find('tbody')
                    if tbody and tbody.find_all('tr'):
                        break  # Table found with data, exit retry loop
                    elif retry < max_retries - 1:
                        print(f"  ⚠ Table found but no data rows, retrying... ({retry + 1}/{max_retries})")
                        await asyncio.sleep(2)
                        continue

                if retry < max_retries - 1:
                    print(f"  ⚠ No table found, retrying... ({retry + 1}/{max_retries})")
                    await asyncio.sleep(2)

            if not card_table:
                print(f"  ✗ No table found after {max_retries} retries")
                return None

            # Extract headers - check all potential header rows
            headers = []
            thead = card_table.find('thead')
            if thead:
                # Get all th elements, even if they're in tbody (common in some tables)
                all_ths = thead.find_all('th')
                headers = [th.get_text(strip=True) for th in all_ths]
            
            # If no headers in thead, check first row in tbody
            if not headers:
                tbody = card_table.find('tbody')
                if tbody:
                    first_row = tbody.find('tr')
                    if first_row:
                        ths = first_row.find_all('th')
                        if ths:
                            headers = [th.get_text(strip=True) for th in ths]

            # Extract rows from tbody
            rows = []
            tbody = card_table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    # Skip header rows (rows with th elements)
                    if tr.find('th'):
                        continue
                    cells = tr.find_all('td')
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    # Only add rows with actual data (not empty)
                    if row_data and any(cell.strip() for cell in row_data):
                        rows.append(row_data)

            print(f"  ✓ Extracted {len(rows)} rows with {len(headers)} headers")

            # Create DataFrame
            if rows:
                # If headers don't match column count, generate column names
                if headers and len(headers) != len(rows[0]) if rows else 0:
                    print(f"    Note: Header/column mismatch ({len(headers)} vs {len(rows[0]) if rows else 0}), using auto-generated column names")
                    # Get the maximum number of columns
                    max_cols = max(len(row) for row in rows) if rows else 0
                    # Generate column names if needed
                    if headers and len(headers) > 0:
                        # Use headers for available columns, auto-generate for the rest
                        column_names = headers + [f'Column_{i}' for i in range(len(headers), max_cols)]
                    else:
                        column_names = [f'Column_{i}' for i in range(max_cols)]
                    df = pd.DataFrame(rows, columns=column_names[:max_cols] if max_cols > 0 else None)
                else:
                    df = pd.DataFrame(rows, columns=headers if headers else None)

                return df

            print(f"  ℹ Table found but no data rows")
            return None

        except Exception as e:
            print(f"  ✗ Error extracting table: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_all_dates(self, page, button_text, output_dir="smlog_data"):
        """Process data for all dates for a specific button - saves individual CSV per date"""
        print(f"\n" + "=" * 70)
        print(f"PROCESSING: {button_text}")
        print("=" * 70)

        # Create output directory with button name subdirectory
        button_output_dir = os.path.join(output_dir, button_text)
        os.makedirs(button_output_dir, exist_ok=True)

        # Click the button
        if not await self.find_and_click_button(page, button_text):
            print(f"✗ Could not click button: {button_text}")
            return False

        current_date = self.start_date
        today = datetime.now()

        # Calculate the limit date
        if self.days_limit:
            limit_date = self.start_date + timedelta(days=self.days_limit - 1)
            today = min(today, limit_date)

        # Track success/failure
        success_count = 0
        failed_dates = []

        # Iterate through dates
        while current_date <= today:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\n[{date_str}] Processing date...")

            # Set date range
            if await self.set_date_range(page, current_date):
                # Wait a bit more to ensure data is loaded
                await asyncio.sleep(2)
                
                # Extract data
                df = await self.extract_table_data(page)

                if df is not None and len(df) > 0:
                    # Add date column
                    df['date'] = date_str
                    
                    # Save individual CSV file for this date
                    csv_filename = os.path.join(button_output_dir, f"{date_str}_{button_text}.csv")
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ CSV saved: {csv_filename} ({len(df)} rows)")
                    success_count += 1
                else:
                    print(f"  ℹ No data for {date_str}")
                    failed_dates.append(date_str)
            else:
                print(f"  ✗ Could not set date for {date_str}")
                failed_dates.append(date_str)

            # Move to next date
            current_date += timedelta(days=1)

            # Delay between date requests to avoid overwhelming the server
            await asyncio.sleep(1)

        # Summary
        print(f"\n" + "=" * 70)
        print(f"SUMMARY for {button_text}")
        print("=" * 70)
        print(f"  ✓ Successfully saved: {success_count} dates")
        if failed_dates:
            print(f"  ✗ Failed dates: {len(failed_dates)}")
            if len(failed_dates) <= 10:
                print(f"    {', '.join(failed_dates)}")
            else:
                print(f"    {', '.join(failed_dates[:10])} ... and {len(failed_dates) - 10} more")
        print("=" * 70)

        return success_count > 0

    async def run(self):
        """Main execution"""
        print("=" * 70)
        print("SMLOG Detailed Data Scraper")
        print("=" * 70)

        # Calculate end date
        today = datetime.now()
        if self.days_limit:
            end_date = self.start_date + timedelta(days=self.days_limit - 1)
            end_date = min(end_date, today)
            num_days = (end_date - self.start_date).days + 1
        else:
            end_date = today
            num_days = (end_date - self.start_date).days + 1

        print(f"\nDate Range: {self.start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Total days: {num_days}")
        print(f"Buttons to scrape: {', '.join(self.buttons_to_scrape)}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Login and navigate
                if not await self.login_and_navigate(page):
                    print("\n✗ Navigation failed")
                    return False

                # Process each button
                results = {}
                for button_text in self.buttons_to_scrape:
                    try:
                        success = await self.process_all_dates(page, button_text)
                        results[button_text] = "✓ Success" if success else "✗ Failed"
                    except Exception as e:
                        print(f"\n✗ Error processing {button_text}: {e}")
                        results[button_text] = f"✗ Error: {e}"

                # Summary
                print("\n" + "=" * 70)
                print("SUMMARY")
                print("=" * 70)
                for button_text, status in results.items():
                    print(f"  {button_text}: {status}")
                print("=" * 70)

                return True

            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()
                return False

            finally:
                await browser.close()


if __name__ == '__main__':
    # Load credentials from CSV file
    import os
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'info_smlog.csv')
    if not os.path.exists(csv_path):
        csv_path = '../data/info_smlog.csv'
    
    try:
        creds_df = pd.read_csv(csv_path)
        username = creds_df['usr'].iloc[0]
        password = creds_df['usrs'].iloc[0]
        svid = str(creds_df['svid'].iloc[0])
        print(f"✓ Credentials loaded from {csv_path}")
    except Exception as e:
        print(f"✗ Error loading credentials from CSV: {e}")
        print("Please ensure data/info_smlog.csv exists with columns: usr, usrs, svid")
        raise

    # Scrape ALL data from 2025-08-18 to today
    days_to_scrape = None  # None = all data from 2025-08-18 to today

    scraper = SMLogDetailedScraper(
        username,
        password,
        svid,
        start_date=datetime(2025, 11, 17),
        days_limit=days_to_scrape
    )
    asyncio.run(scraper.run())
