#!/usr/bin/env python3
"""
Final test to see the complete Wise flow and result
"""
import asyncio
from playwright.async_api import async_playwright
import re

async def test_wise_complete_flow():
    """Test complete Wise flow and see result"""
    try:
        print("🧪 Testing complete Wise flow...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Navigate
            await page.goto("https://wise.com/ca/iban/calculator")
            await page.wait_for_load_state('networkidle')
            print("✅ Page loaded")
            
            # Select country
            await page.click('button:has-text("Select a Country")')
            await page.wait_for_timeout(1000)
            await page.click('text=United Kingdom')
            await page.wait_for_timeout(2000)
            print("✅ UK selected")
            
            # Fill form
            await page.fill('input[name="branch_code"]', '200000')
            await page.fill('input[name="account_number"]', '55779911')
            print("✅ Form filled")
            
            # Click calculate
            await page.click('button:has-text("Calculate IBAN")')
            await page.wait_for_timeout(5000)
            print("✅ Calculate clicked")
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Take screenshot
            await page.screenshot(path='wise_final_result.png')
            
            # Get page content
            content = await page.content()
            
            # Save HTML
            with open('wise_final_result.html', 'w') as f:
                f.write(content)
            
            print("💾 Saved screenshot and HTML")
            
            # Look for IBAN patterns
            print("\n🔍 Looking for IBAN patterns...")
            
            # Method 1: UK IBAN pattern
            uk_iban = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', content)
            if uk_iban:
                print(f"✅ Found UK IBAN: {uk_iban.group(1)}")
                
            # Method 2: Any IBAN pattern
            any_iban = re.findall(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', content)
            if any_iban:
                print(f"✅ Found IBAN patterns: {any_iban}")
                
            # Method 3: Look for specific text
            if "GB" in content:
                print("✅ 'GB' found in content")
                # Find lines with GB
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'GB' in line and len(line.strip()) > 10:
                        print(f"   Line {i}: {line.strip()[:100]}...")
            
            # Method 4: Look in all visible text
            all_text = await page.evaluate('document.body.innerText')
            print(f"\n📄 Page text length: {len(all_text)}")
            
            # Look for IBAN in visible text
            visible_iban = re.search(r'\b(GB[0-9]{2}[A-Z0-9]{18})\b', all_text)
            if visible_iban:
                print(f"✅ Found IBAN in visible text: {visible_iban.group(1)}")
            else:
                print("❌ No IBAN in visible text")
                # Show some visible text
                print(f"Sample visible text: {all_text[:500]}...")
            
            # Wait for manual inspection
            print(f"\n👀 Waiting 15 seconds for manual inspection...")
            await page.wait_for_timeout(15000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_wise_complete_flow())