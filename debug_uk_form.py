#!/usr/bin/env python3
"""
Quick debug for UK bank form to see what's returned
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def debug_uk_form():
    """Debug UK form submission"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visual mode
            page = await browser.new_page()
            
            print("🔍 Debugging UK IBAN form...")
            
            # Navigate to IBAN calculator
            await page.goto("https://www.iban.com/calculate-iban")
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Select UK
            await page.select_option('select[name="country"]', 'GB')
            await page.wait_for_timeout(2000)
            
            print("✅ Selected GB")
            
            # Fill with the failing case
            await page.fill('input[name="bankcode"]', '111702')
            await page.fill('input[name="account"]', '14114666')
            
            print("✅ Form filled")
            
            # Submit
            await page.click('input[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=20000)
            
            print("✅ Form submitted")
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Save for inspection
            with open('uk_debug.html', 'w') as f:
                f.write(content)
            
            print("\n📋 All input fields after submission:")
            inputs = soup.find_all('input')
            for i, inp in enumerate(inputs):
                name = inp.get('name', 'N/A')
                value = inp.get('value', 'N/A')
                input_type = inp.get('type', 'N/A')
                print(f"  {i+1}. name='{name}', value='{value}', type='{input_type}'")
            
            print("\n🔍 Looking for IBAN patterns:")
            
            # Look for GB IBAN pattern
            gb_patterns = re.findall(r'\b(GB[0-9]{2}[A-Z0-9]{18})\b', content)
            if gb_patterns:
                print(f"✅ Found GB IBAN patterns: {gb_patterns}")
            else:
                print("❌ No GB IBAN patterns found")
            
            # Look for any IBAN pattern
            any_patterns = re.findall(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', content)
            if any_patterns:
                print(f"✅ Found IBAN patterns: {any_patterns}")
            else:
                print("❌ No IBAN patterns found")
            
            # Look for specific text
            if "GB" in content:
                print("✅ 'GB' found in page")
                # Find context around GB
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'GB' in line and len(line.strip()) > 2:
                        print(f"   Line {i}: {line.strip()[:100]}...")
            else:
                print("❌ 'GB' not found in page")
            
            # Check for error messages
            error_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'error|alert|warning', re.I))
            if error_elements:
                print(f"\n⚠️ Found {len(error_elements)} potential error elements:")
                for elem in error_elements:
                    text = elem.get_text().strip()
                    if text:
                        print(f"   - {text}")
            
            # Wait for manual inspection
            print(f"\n👀 Waiting 10 seconds for manual inspection...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_uk_form())