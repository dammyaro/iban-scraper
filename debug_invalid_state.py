#!/usr/bin/env python3
"""
Debug the invalid state error
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_invalid_state():
    """Debug the invalid state issue"""
    try:
        print("🔍 Debugging invalid state error...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Navigate
                print("1. Navigating...")
                await page.goto("https://wise.com/ca/iban/calculator")
                await page.wait_for_load_state('networkidle')
                print("✅ Page loaded")
                
                # Select country
                print("2. Selecting country...")
                await page.click('button:has-text("Select a Country")')
                await page.wait_for_timeout(1000)
                await page.click('text=United Kingdom')
                await page.wait_for_timeout(2000)
                print("✅ UK selected")
                
                # Fill form
                print("3. Filling form...")
                await page.fill('input[name="branch_code"]', '200000')
                await page.fill('input[name="account_number"]', '55779911')
                print("✅ Form filled")
                
                # Click calculate
                print("4. Clicking calculate...")
                await page.click('button:has-text("Calculate IBAN")')
                print("✅ Calculate clicked")
                
                # Wait more conservatively
                print("5. Waiting for result...")
                await page.wait_for_timeout(3000)
                
                # Check if page is still valid
                try:
                    title = await page.title()
                    print(f"✅ Page title: {title}")
                except Exception as e:
                    print(f"❌ Page title error: {e}")
                
                # Try to get content
                try:
                    content = await page.content()
                    print(f"✅ Content length: {len(content)}")
                    
                    # Look for IBAN
                    import re
                    iban_match = re.search(r'\b(GB[0-9]{2}[A-Z0-9]{18})\b', content)
                    if iban_match:
                        print(f"🎉 IBAN found: {iban_match.group(1)}")
                    else:
                        print("❌ No IBAN found")
                        
                except Exception as e:
                    print(f"❌ Content error: {e}")
                
                # Wait for inspection
                print("👀 Waiting 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"❌ Step failed: {e}")
            
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_invalid_state())