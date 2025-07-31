#!/usr/bin/env python3
"""
Simple test to understand Wise interface better
"""
import asyncio
from playwright.async_api import async_playwright

async def test_wise_simple():
    """Simple test of Wise interface"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print("🔍 Testing Wise interface...")
            
            # Navigate to Wise
            await page.goto("https://wise.com/ca/iban/calculator")
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Wait and let user see the page
            print("👀 Inspect the page manually...")
            print("Look for:")
            print("1. How to select country")
            print("2. Where to enter bank details")
            print("3. How the form works")
            
            # Wait 30 seconds for manual inspection
            await page.wait_for_timeout(30000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_wise_simple())