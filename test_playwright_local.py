#!/usr/bin/env python3
"""
Test script to verify Playwright setup locally
"""
import asyncio
import sys
from playwright.async_api import async_playwright

async def test_playwright_setup():
    """Test if Playwright can launch and navigate"""
    try:
        print("🧪 Testing Playwright setup...")
        
        async with async_playwright() as p:
            print("✅ Playwright imported successfully")
            
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            print("✅ Chromium browser launched")
            
            # Create page
            page = await browser.new_page()
            print("✅ New page created")
            
            # Navigate to a simple page
            await page.goto("https://www.iban.com/calculate-iban")
            print("✅ Navigated to IBAN calculator")
            
            # Check if page loaded
            title = await page.title()
            print(f"✅ Page title: {title}")
            
            # Check if form elements exist
            country_select = await page.query_selector('select[name="country"]')
            bank_input = await page.query_selector('input[name="bankcode"]')
            account_input = await page.query_selector('input[name="account"]')
            
            if country_select and bank_input and account_input:
                print("✅ All form elements found")
            else:
                print("❌ Some form elements missing")
            
            await browser.close()
            print("✅ Browser closed successfully")
            
        print("\n🎉 Playwright setup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Playwright test failed: {e}")
        return False

async def test_iban_calculation():
    """Test actual IBAN calculation"""
    try:
        print("\n🧪 Testing IBAN calculation...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to IBAN calculator
            await page.goto("https://www.iban.com/calculate-iban")
            
            # Fill form with German bank details
            await page.select_option('select[name="country"]', 'DE')
            await page.wait_for_timeout(1000)  # Wait for form update
            
            await page.fill('input[name="bankcode"]', '37040044')
            await page.fill('input[name="account"]', '532013000')
            
            # Submit form
            await page.click('input[type="submit"]')
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Try to extract IBAN
            iban_input = await page.query_selector('#iban')
            if iban_input:
                iban_value = await iban_input.get_attribute('value')
                if iban_value:
                    print(f"✅ IBAN calculated: {iban_value}")
                    await browser.close()
                    return True
            
            # Fallback: check page content
            content = await page.content()
            if 'DE89370400440532013000' in content:
                print("✅ IBAN found in page content")
                await browser.close()
                return True
            
            print("❌ Could not extract IBAN")
            await browser.close()
            return False
            
    except Exception as e:
        print(f"❌ IBAN calculation test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Playwright local tests...\n")
    
    # Test 1: Basic Playwright setup
    setup_ok = await test_playwright_setup()
    
    if setup_ok:
        # Test 2: IBAN calculation
        calc_ok = await test_iban_calculation()
        
        if calc_ok:
            print("\n🎉 All tests passed! Playwright is ready for production.")
            sys.exit(0)
        else:
            print("\n❌ IBAN calculation failed. Check the implementation.")
            sys.exit(1)
    else:
        print("\n❌ Playwright setup failed. Install with: playwright install chromium")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())