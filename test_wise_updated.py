#!/usr/bin/env python3
"""
Test the updated Wise IBAN calculator implementation
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def test_wise_uk_iban():
    """Test UK IBAN calculation with Wise"""
    try:
        print("🧪 Testing Wise IBAN calculator with UK bank details...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visual mode
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            # Navigate to Wise IBAN calculator
            print("📍 Navigating to Wise...")
            await page.goto("https://wise.com/ca/iban/calculator", timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Step 1: Click on country dropdown
            print("🌍 Opening country dropdown...")
            await page.click('button:has-text("Select a Country")')
            await page.wait_for_timeout(1000)
            
            # Step 2: Select United Kingdom
            print("🇬🇧 Selecting United Kingdom...")
            await page.click('text=United Kingdom')
            await page.wait_for_timeout(2000)
            
            print("✅ Country selected, form should transform now")
            
            # Step 3: Fill sort code
            print("🏦 Filling sort code...")
            bank_input = await page.query_selector('input[placeholder*="sort"], input[placeholder*="bank"], input[name*="bank"]')
            if bank_input:
                await bank_input.fill('200000')
                print("✅ Sort code filled")
            else:
                print("❌ Could not find sort code input")
                # Try fallback
                await page.fill('input:nth-of-type(1)', '200000')
                print("✅ Sort code filled (fallback)")
            
            # Step 4: Fill account number
            print("💳 Filling account number...")
            account_input = await page.query_selector('input[placeholder*="account"], input[name*="account"]')
            if account_input:
                await account_input.fill('55779911')
                print("✅ Account number filled")
            else:
                print("❌ Could not find account input")
                # Try fallback
                await page.fill('input:nth-of-type(2)', '55779911')
                print("✅ Account number filled (fallback)")
            
            # Step 5: Click calculate
            print("🔢 Clicking Calculate IBAN...")
            await page.click('button:has-text("Calculate IBAN")')
            await page.wait_for_timeout(3000)
            
            print("✅ Calculate button clicked, waiting for result...")
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Look for IBAN in result
            print("🔍 Looking for IBAN in result...")
            
            # Method 1: Look in result elements
            result_elements = await page.query_selector_all('.result, .iban-result, [class*="result"], [class*="iban"]')
            iban_found = None
            
            for element in result_elements:
                text = await element.text_content()
                if text:
                    text = text.strip()
                    if len(text) >= 15 and re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', text):
                        iban_found = text
                        print(f"✅ Found IBAN in result element: {iban_found}")
                        break
            
            # Method 2: Look in all page text
            if not iban_found:
                print("🔍 Searching all page text...")
                page_content = await page.content()
                
                # Look for UK IBAN pattern
                uk_iban = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', page_content)
                if uk_iban:
                    iban_found = uk_iban.group(1)
                    print(f"✅ Found UK IBAN: {iban_found}")
                else:
                    # Look for any IBAN pattern
                    any_iban = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', page_content)
                    if any_iban:
                        iban_found = any_iban.group(1)
                        print(f"✅ Found IBAN: {iban_found}")
            
            if not iban_found:
                print("❌ No IBAN found")
                
                # Save page for debugging
                await page.screenshot(path='wise_test_result.png')
                content = await page.content()
                with open('wise_test_result.html', 'w') as f:
                    f.write(content)
                print("💾 Saved screenshot and HTML for debugging")
            
            # Wait for manual inspection
            print("👀 Waiting 10 seconds for manual inspection...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
            return iban_found
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

async def test_api_with_wise():
    """Test our API with the updated Wise implementation"""
    print("\n🧪 Testing API with Wise implementation...")
    
    import requests
    
    try:
        response = requests.post(
            "http://localhost:8000/calculate-iban",
            json={
                "country_code": "GB",
                "bank_code": "200000", 
                "account_number": "55779911"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Success: {data}")
            return data
        else:
            print(f"❌ API Failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API Test failed: {e}")
        return None

async def main():
    """Run all tests"""
    print("🚀 Testing Updated Wise Implementation")
    print("=" * 50)
    
    # Test 1: Direct Playwright test
    iban_direct = await test_wise_uk_iban()
    
    # Test 2: API test
    iban_api = await test_api_with_wise()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"Direct Playwright: {iban_direct or 'Failed'}")
    print(f"API Test: {iban_api.get('iban') if iban_api else 'Failed'}")
    
    if iban_direct or (iban_api and iban_api.get('iban')):
        print("\n🎉 Success! Wise implementation is working.")
    else:
        print("\n❌ Tests failed. Need to debug further.")

if __name__ == "__main__":
    asyncio.run(main())