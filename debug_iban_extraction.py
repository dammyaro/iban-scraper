#!/usr/bin/env python3
"""
Debug script to see what happens after form submission
"""
import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_iban_extraction():
    """Debug the IBAN extraction after form submission"""
    try:
        print("🔍 Debugging IBAN extraction...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Run with GUI
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Navigate to IBAN calculator
            await page.goto("https://www.iban.com/calculate-iban")
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Fill form with German bank details
            await page.select_option('select[name="country"]', 'DE')
            await page.wait_for_timeout(1000)
            
            await page.fill('input[name="bankcode"]', '37040044')
            await page.fill('input[name="account"]', '532013000')
            
            print("✅ Form filled")
            
            # Submit form
            await page.click('input[type="submit"]')
            print("✅ Form submitted")
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            print("✅ Page loaded after submission")
            
            # Get current URL
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            # Take screenshot
            await page.screenshot(path='after_submission.png')
            print("📸 Screenshot saved as 'after_submission.png'")
            
            # Get page content
            page_content = await page.content()
            
            # Save HTML for inspection
            with open('page_after_submission.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("💾 HTML saved as 'page_after_submission.html'")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Look for all input fields
            print("\n📋 All input fields after submission:")
            inputs = soup.find_all('input')
            for i, input_elem in enumerate(inputs):
                input_type = input_elem.get('type', 'N/A')
                input_name = input_elem.get('name', 'N/A')
                input_value = input_elem.get('value', 'N/A')
                input_id = input_elem.get('id', 'N/A')
                print(f"  Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', value='{input_value}'")
            
            # Look for IBAN patterns in text
            print("\n🔍 Searching for IBAN patterns:")
            
            # Method 1: German IBAN pattern
            german_iban = re.search(r'\b(DE[0-9]{2}[A-Z0-9]{16,18})\b', page_content)
            if german_iban:
                print(f"✅ Found German IBAN: {german_iban.group(1)}")
            else:
                print("❌ No German IBAN pattern found")
            
            # Method 2: Any IBAN pattern
            any_iban = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', page_content)
            if any_iban:
                print(f"✅ Found IBAN pattern: {any_iban.group(1)}")
            else:
                print("❌ No IBAN pattern found")
            
            # Method 3: Look for the expected IBAN
            expected_iban = "DE89370400440532013000"
            if expected_iban in page_content:
                print(f"✅ Found expected IBAN: {expected_iban}")
            else:
                print(f"❌ Expected IBAN {expected_iban} not found")
            
            # Method 4: Look for any 22-character alphanumeric string starting with DE
            de_strings = re.findall(r'\bDE[A-Z0-9]{20}\b', page_content)
            if de_strings:
                print(f"✅ Found DE strings: {de_strings}")
            else:
                print("❌ No DE strings found")
            
            # Look for result containers
            print("\n📦 Result containers:")
            result_containers = soup.find_all(['div', 'span', 'p', 'td'], 
                                            class_=re.compile(r'result|iban|output|answer', re.I))
            for i, container in enumerate(result_containers):
                print(f"  Container {i+1}: {container.get('class')} - {container.get_text()[:100]}...")
            
            # Wait for manual inspection
            print("\n⏳ Waiting 10 seconds for manual inspection...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_iban_extraction())