#!/usr/bin/env python3
"""
네이버 스마트플레이스 로그인 자동화

요구사항
  - Playwright 사용
  - task.md에 정의된 로그인/토글 규칙 준수
  - 기존 SMLogDetailedScraper와 유사한 로깅/흐름 유지
"""

import asyncio
import os
from dataclasses import dataclass

import pandas as pd
from playwright.async_api import async_playwright, Page


@dataclass
class LoginSelectors:
    id_input_candidates: tuple = (
        "#input_item_id input",
        "input#id",
        "input[name='id']",
        "input[type='text'][name='id']",
    )
    pw_input_candidates: tuple = (
        "#input_item_pw input",
        "input#pw",
        "input[name='pw']",
        "input[type='password'][name='pw']",
    )
    ip_toggle_label: str = "#login_keep_wrap > div.ip_check > span > label"
    login_button: str = "#log\\.login"
    ip_checkbox_candidates: tuple = (
        "#ip_on",
        "#keep_login",
        "#keep_login_chk",
        "#login_keep_wrap input[type='checkbox']",
    )
    search_button_selectors: tuple = (
        "#search_btn",
        ".btn-container-search",
        "div.btn-container-search",
        "[id='search_btn']",
    )


class NaverPlaceLogin:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.login_url = (
            "https://nid.naver.com/nidlogin.login"
            "?svctype=1&locale=ko_KR&url=https%3A%2F%2Fnew.smartplace.naver.com%2F&area=bbt"
        )
        self.base_url = (
            "https://new.smartplace.naver.com/bizes/place/5921383"
            "?bookingBusinessId=603738"
        )
        self.selectors = LoginSelectors()

    async def fill_text_input(
        self, page: Page, selectors: tuple, value: str, field_name: str
    ) -> bool:
        """Try multiple selectors until the text field is filled."""
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if await locator.count() == 0:
                    continue
                target = locator.first
                await target.fill("")
                await target.fill(value)
                print(f"  ✓ {field_name} filled via selector: {selector}")
                return True
            except Exception as e:
                print(f"  ⚠ Failed to fill {field_name} with {selector}: {e}")
                continue

        print(f"  ✗ Could not fill {field_name} (selectors exhausted)")
        return False

    async def is_login_form_visible(self, page: Page) -> bool:
        """Check if login ID input is still visible."""
        for selector in self.selectors.id_input_candidates:
            try:
                if await page.is_visible(selector):
                    return True
            except Exception:
                continue
        return False

    async def toggle_ip_security_off(self, page: Page) -> None:
        """Ensure the IP security toggle is OFF."""
        print("\n[Login] Checking IP security toggle...")
        checkbox = None
        for selector in self.selectors.ip_checkbox_candidates:
            checkbox = await page.query_selector(selector)
            if checkbox:
                print(f"  Found checkbox selector: {selector}")
                break

        if checkbox:
            try:
                is_checked = await checkbox.is_checked()
            except Exception:
                is_checked = None
        else:
            is_checked = None

        toggle_label = await page.query_selector(self.selectors.ip_toggle_label)
        if not toggle_label:
            print("  ⚠ IP security toggle label not found, skipping")
            return

        if is_checked is None:
            print("  ℹ Checkbox state unknown, clicking label once to ensure OFF")
            await toggle_label.click()
            await asyncio.sleep(0.5)
            return

        if is_checked:
            print("  IP security is ON → toggling OFF")
            await toggle_label.click()
            await asyncio.sleep(0.5)
            if await checkbox.is_checked():
                print("  ⚠ Toggle still ON, clicking again")
                await toggle_label.click()
                await asyncio.sleep(0.5)
        else:
            print("  IP security already OFF")

    async def perform_login(self, page: Page) -> bool:
        """Complete the login sequence."""
        print("\n[Login] Starting login sequence...")
        await page.goto(self.login_url, wait_until="networkidle")
        await asyncio.sleep(1)

        print("  Filling ID/PW...")
        id_filled = await self.fill_text_input(
            page, self.selectors.id_input_candidates, self.username, "ID"
        )
        pw_filled = await self.fill_text_input(
            page, self.selectors.pw_input_candidates, self.password, "Password"
        )
        if not (id_filled and pw_filled):
            print("  ✗ Unable to fill ID or Password field")
            return False
        await asyncio.sleep(0.5)

        await self.toggle_ip_security_off(page)

        print("  Clicking login button...")
        await page.click(self.selectors.login_button)

        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            print("  ⚠ Login page did not reach networkidle, continuing")
        await asyncio.sleep(1.5)

        # Simple validation: check if login input still visible
        if await self.is_login_form_visible(page):
            print("  ✗ Login might have failed (ID input still visible)")
            return False

        print("  ✓ Login successful")
        return True

    async def navigate_to_base(self, page: Page) -> bool:
        """Navigate to the base SmartPlace URL after login."""
        print("\n[Navigation] Moving to base dashboard...")
        await page.goto(self.base_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        if "smartplace.naver.com" in page.url:
            print(f"  ✓ Arrived at {page.url}")
            return True

        print(f"  ⚠ Unexpected URL after navigation: {page.url}")
        return False

    async def run(self) -> bool:
        """Main execution entry."""
        print("=" * 70)
        print("Naver SmartPlace Login Automation")
        print("=" * 70)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                if not await self.perform_login(page):
                    return False

                result = await self.navigate_to_base(page)
                return result
            finally:
                await browser.close()


def load_credentials():
    """Load credentials from CSV (supports path with/without .csv)."""
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "info_naver.csv"
    )
    if not os.path.exists(csv_path):
        alt_path = os.path.join(os.path.dirname(__file__), "..", "data", "info_naver")
        if os.path.exists(alt_path):
            csv_path = alt_path
        else:
            raise FileNotFoundError(
                "info_naver(.csv) not found in ../data/"
            )

    creds = pd.read_csv(csv_path)
    username = creds.iloc[0, 0]
    password = creds.iloc[0, 1]
    print(f"✓ Credentials loaded from {csv_path}")
    return username, password


if __name__ == "__main__":
    usr, pwd = load_credentials()
    login = NaverPlaceLogin(usr, pwd)
    asyncio.run(login.run())

