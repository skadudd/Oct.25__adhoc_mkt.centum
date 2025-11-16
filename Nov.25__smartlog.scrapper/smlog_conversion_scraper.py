#!/usr/bin/env python3
"""
SMLOG Conversion Summary Scraper
Extracts data from conversion summary page (유입유형)
Sets date range from start_date to end_date, iterates day by day
Exports data as CSV/Excel files with date range in filename
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os


class SMLogConversionScraper:
    def __init__(self, username, password, svid="33138", start_date=None, end_date=None, days_limit=None):
        self.username = username
        self.password = password
        self.svid = svid
        self.base_url = "https://smlog.co.kr"
        self.login_url = f"{self.base_url}/2020/member/login.html"
        self.conversion_url = f"{self.base_url}/hmisNew/conversion_summary.html?svid={svid}"

        # Button to scrape
        self.button_text = "유입유형(전체)"

        # Start date (default: 2025-11-05)
        self.start_date = start_date if start_date else datetime(2025, 11, 5)

        # End date (default: today)
        self.end_date = end_date if end_date else datetime.now()

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
            await asyncio.sleep(3)

        # Step 4: Click HMIS button
        print("  [4/5] Clicking HMIS button...")
        hmis_button = await page.query_selector('.hmis')
        if hmis_button:
            await hmis_button.click()
            await asyncio.sleep(3)

        # Step 5: Click service domain link
        print("  [5/5] Clicking service domain link...")
        service_links = await page.query_selector_all('.service-domain-url')
        for link in service_links:
            href = await link.get_attribute('href')
            if href and f"svid={self.svid}" in href:
                await link.click()
                await asyncio.sleep(3)
                break

        # Navigate to conversion summary page
        await page.goto(self.conversion_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        print("✓ Navigation completed successfully")
        return True

    async def find_and_click_button(self, page, button_text):
        """Find and click a button by text (class = page-tab)"""
        print(f"\n[Button] Looking for button: {button_text}")

        try:
            # Find the page-tab element
            tabs = await page.query_selector_all('div.page-tab')
            print(f"  Found {len(tabs)} page tabs")

            for tab in tabs:
                text = await tab.inner_text()
                print(f"    Tab text: '{text}'")
                if text == button_text or button_text in text:
                    print(f"  ✓ Found matching tab: '{text}'")
                    await tab.click()
                    await asyncio.sleep(3)
                    print(f"  ✓ Button clicked")
                    return True

            print(f"  ✗ Button not found in {len(tabs)} tabs")
            return False

        except Exception as e:
            print(f"  ✗ Error finding button: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def set_date(self, page, target_date):
        """Set date using form-control input fields and click apply/search buttons"""
        print(f"\n[Date] Setting date to {target_date.strftime('%Y-%m-%d')}")

        try:
            # Format date as YYYY-MM-DD
            date_str = target_date.strftime('%Y-%m-%d')

            # Find all form-control date inputs
            date_inputs = await page.query_selector_all('input.form-control[type="date"], input.form-control[type="text"]')
            print(f"  Found {len(date_inputs)} form-control inputs")

            if len(date_inputs) >= 2:
                # Set start date (first input)
                await date_inputs[0].fill(date_str)
                print(f"  Set start date: {date_str}")
                await asyncio.sleep(0.5)

                # Set end date (second input) - same date for single day
                await date_inputs[1].fill(date_str)
                print(f"  Set end date: {date_str}")
                await asyncio.sleep(1)

                # Step 1: Click apply button (class = applyBtn btn btn-sm btn-primary)
                apply_button = await page.query_selector('.applyBtn.btn.btn-sm.btn-primary')
                if not apply_button:
                    # Try alternative selector
                    apply_button = await page.query_selector('button.applyBtn')
                
                if apply_button:
                    await apply_button.click()
                    print(f"  ✓ Clicked apply button")
                    await asyncio.sleep(2)
                else:
                    print(f"  ⚠ Apply button not found, trying to continue...")

                # Step 2: Click search button (class = btn-container-search)
                search_button = await page.query_selector('.btn-container-search')
                if not search_button:
                    # Try alternative selectors
                    search_button = await page.query_selector('button.btn-container-search')
                    if not search_button:
                        search_button = await page.query_selector('.btn-search')
                
                if search_button:
                    await search_button.click()
                    print(f"  ✓ Clicked search button")
                    await asyncio.sleep(3)  # Wait for data to load
                else:
                    print(f"  ⚠ Search button not found, trying alternative methods...")
                    # Fallback: try to find any search/submit button
                    search_buttons = await page.query_selector_all('button[type="submit"], button.btn-primary, button.btn-search')
                    if search_buttons:
                        await search_buttons[0].click()
                        await asyncio.sleep(3)
                        print(f"  ✓ Clicked fallback search button")
                    else:
                        print(f"  ✗ No search button found")

                print(f"  ✓ Date set and buttons clicked")
                return True
            elif len(date_inputs) == 1:
                # Single date input
                await date_inputs[0].fill(date_str)
                print(f"  Set date: {date_str}")
                await asyncio.sleep(1)

                # Click apply button
                apply_button = await page.query_selector('.applyBtn.btn.btn-sm.btn-primary')
                if apply_button:
                    await apply_button.click()
                    await asyncio.sleep(2)

                # Click search button
                search_button = await page.query_selector('.btn-container-search')
                if search_button:
                    await search_button.click()
                    await asyncio.sleep(3)
                    print(f"  ✓ Date set and buttons clicked")
                else:
                    print(f"  ⚠ Search button not found")
                
                return True
            else:
                print(f"  ✗ Date input fields not found")
                return False

        except Exception as e:
            print(f"  Error setting date: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def extract_table_data(self, page):
        """Extract table data from table with specific classes"""
        print(f"\n[Table] Extracting table data...")

        try:
            await asyncio.sleep(2)  # Wait for page to load

            soup = BeautifulSoup(await page.content(), 'html.parser')

            # Find the table with specific classes: table table-centered table-nowrap table-hover mb-0 data
            table = soup.find('table', class_=lambda x: x and (
                'table' in str(x).lower() and
                'table-centered' in str(x).lower() and
                'table-nowrap' in str(x).lower() and
                'table-hover' in str(x).lower() and
                'mb-0' in str(x).lower() and
                'data' in str(x).lower()
            ))

            if not table:
                # Try alternative: find table with 'data' class
                table = soup.find('table', class_='data')
                if not table:
                    # Try any table with table-centered
                    table = soup.find('table', class_='table-centered')
                    if not table:
                        # Try any table
                        table = soup.find('table')
                        print(f"  Using fallback table selector")

            if not table:
                print(f"  ✗ No table found")
                return None

            # Extract headers
            headers = []
            thead = table.find('thead')
            if thead:
                all_ths = thead.find_all('th')
                headers = [th.get_text(strip=True) for th in all_ths]

            # Extract rows from tbody
            rows = []
            tbody = table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    cells = tr.find_all('td')
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        rows.append(row_data)

            print(f"  ✓ Extracted {len(rows)} rows with {len(headers)} headers")

            # Create DataFrame
            if rows:
                # If headers don't match column count, generate column names
                if headers and len(headers) != len(rows[0]) if rows else 0:
                    print(f"    Note: Header/column mismatch ({len(headers)} vs {len(rows[0]) if rows else 0}), using auto-generated column names")
                    max_cols = max(len(row) for row in rows) if rows else 0
                    if headers and len(headers) > 0:
                        column_names = headers + [f'Column_{i}' for i in range(len(headers), max_cols)]
                    else:
                        column_names = [f'Column_{i}' for i in range(max_cols)]
                    df = pd.DataFrame(rows, columns=column_names[:max_cols] if max_cols > 0 else None)
                else:
                    df = pd.DataFrame(rows, columns=headers if headers else None)

                return df

            return None

        except Exception as e:
            print(f"  ✗ Error extracting table: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_all_dates(self, page, output_dir="smlog_data"):
        """Process data for all dates"""
        print(f"\n" + "=" * 70)
        print(f"PROCESSING: {self.button_text}")
        print("=" * 70)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Click the button
        if not await self.find_and_click_button(page, self.button_text):
            print(f"✗ Could not click button: {self.button_text}")
            return False

        all_data = []
        current_date = self.start_date
        today = datetime.now()

        # Calculate the limit date
        end_date = self.end_date
        if self.days_limit:
            limit_date = self.start_date + timedelta(days=self.days_limit - 1)
            end_date = min(end_date, limit_date)
        end_date = min(end_date, today)

        # Track actual date range for filename
        first_date = None
        last_date = None

        # Iterate through dates
        date_count = 0
        while current_date <= end_date:
            print(f"\n[{current_date.strftime('%Y-%m-%d')}] Processing date...")

            # Set date
            if await self.set_date(page, current_date):
                # Extract data
                df = await self.extract_table_data(page)

                if df is not None and len(df) > 0:
                    df['date'] = current_date.strftime('%Y-%m-%d')
                    all_data.append(df)
                    date_count += 1

                    # Track date range
                    if first_date is None:
                        first_date = current_date
                    last_date = current_date

                    print(f"  ✓ Data extracted for {current_date.strftime('%Y-%m-%d')} ({len(df)} rows)")
                else:
                    print(f"  ℹ No data for {current_date.strftime('%Y-%m-%d')}")
            else:
                print(f"  ✗ Could not set date")
                break

            # Move to next date
            current_date += timedelta(days=1)

            # Minimal delay between date requests
            await asyncio.sleep(0.5)

        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)

            # Determine date range for filename
            if first_date and last_date:
                start_date_str = first_date.strftime('%Y-%m-%d')
                end_date_str = last_date.strftime('%Y-%m-%d')
            else:
                # Fallback to start_date and end_date if no data collected
                start_date_str = self.start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')

            # Export with naming convention: {start_date}_{end_date}_{button_text}
            button_name = self.button_text.replace('(', '').replace(')', '').replace(' ', '_')
            filename = f"{output_dir}/{start_date_str}_{end_date_str}_{button_name}"
            csv_file = f"{filename}.csv"
            excel_file = f"{filename}.xlsx"

            print(f"\n[Export] Saving {self.button_text}...")
            combined_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  ✓ CSV exported: {csv_file}")

            combined_df.to_excel(excel_file, index=False, engine='openpyxl')
            print(f"  ✓ Excel exported: {excel_file}")

            print(f"\n✓ {self.button_text} complete: {len(combined_df)} rows from {date_count} dates")
            return True
        else:
            print(f"✗ No data collected for {self.button_text}")
            return False

    async def run(self):
        """Main execution"""
        print("=" * 70)
        print("SMLOG Conversion Summary Scraper")
        print("=" * 70)

        # Calculate end date
        today = datetime.now()
        end_date = self.end_date
        if self.days_limit:
            limit_date = self.start_date + timedelta(days=self.days_limit - 1)
            end_date = min(end_date, limit_date)
        end_date = min(end_date, today)

        num_days = (end_date - self.start_date).days + 1

        print(f"\nDate Range: {self.start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Total days: {num_days}")
        print(f"Button to scrape: {self.button_text}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Login and navigate
                if not await self.login_and_navigate(page):
                    print("\n✗ Navigation failed")
                    return False

                # Process the button
                try:
                    success = await self.process_all_dates(page)
                    result = "✓ Success" if success else "✗ Failed"
                except Exception as e:
                    print(f"\n✗ Error processing {self.button_text}: {e}")
                    import traceback
                    traceback.print_exc()
                    result = f"✗ Error: {e}"

                # Summary
                print("\n" + "=" * 70)
                print("SUMMARY")
                print("=" * 70)
                print(f"  {self.button_text}: {result}")
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

    # Scrape data from start_date to end_date
    days_to_scrape = None  # None = all data from start_date to end_date

    scraper = SMLogConversionScraper(
        username,
        password,
        svid,
        start_date=datetime(2025, 10, 18),
        end_date=datetime.now(),
        days_limit=days_to_scrape
    )
    asyncio.run(scraper.run())

