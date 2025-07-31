#!/usr/bin/env python3
"""
Debug script to inspect the IBAN calculator page structure
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_page_structure():
    """Debug the page structure to find correct selectors"""
    try:
        print("🔍 Debugging IBAN calculator page structure...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Run with GUI for debugging
            page = await browser.new_page()
            
            # Navigate to IBAN calculator
            await page.goto("https://www.iban.com/calculate-iban")
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Get page title
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Check for different possible selectors
            selectors_to_check = [
                '#country',
                'select[name="country"]',
                'select[id="country"]',
                '.country-select',
                '#bank',
                'input[name="bank"]',
                'input[id="bank"]',
                '#account', 
                'input[name="account"]',
                'input[id="account"]',
                'button[type="submit"]',
                '.submit-btn',
                '#submit'
            ]
            
            print("\n🔍 Checking selectors:")
            for selector in selectors_to_check:
                element = await page.query_selector(selector)
                if element:
                    tag_name = await element.evaluate('el => el.tagName')
                    print(f"✅ Found: {selector} ({tag_name})")
                else:
                    print(f"❌ Missing: {selector}")
            
            # Get all form elements
            print("\n📋 All form elements:")
            forms = await page.query_selector_all('form')
            for i, form in enumerate(forms):
                print(f"\nForm {i+1}:")
                inputs = await form.query_selector_all('input, select, button')
                for input_elem in inputs:
                    tag_name = await input_elem.evaluate('el => el.tagName')
                    input_type = await input_elem.evaluate('el => el.type || "N/A"')
                    input_id = await input_elem.evaluate('el => el.id || "N/A"')
                    input_name = await input_elem.evaluate('el => el.name || "N/A"')
                    input_class = await input_elem.evaluate('el => el.className || "N/A"')
                    print(f"  {tag_name}: id='{input_id}', name='{input_name}', type='{input_type}', class='{input_class}'")
            
            # Take a screenshot for visual inspection
            await page.screenshot(path='iban_page_debug.png')
            print("\n📸 Screenshot saved as 'iban_page_debug.png'")
            
            # Wait a bit so we can see the page
            print("\n⏳ Waiting 5 seconds for manual inspection...")
            await page.wait_for_timeout(5000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_page_structure())