#!/usr/bin/env python3
"""
Debug script that exactly matches the API flow to see where the timeout occurs
"""
import asyncio
from playwright.async_api import async_playwright
import re
import time

async def debug_api_flow():
    """Debug the exact same flow as the API"""
    try:
        print("🔍 Debugging API flow exactly...")
        
        start_time = time.time()
        
        async with async_playwright() as p:
            print(f"⏱️  Playwright started: {time.time() - start_time:.2f}s")
            
            # Launch browser (same settings as API)
            browser = await p.chromium.launch(
                headless=False,  # Visual mode for debugging
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--single-process',
                    '--no-zygote'
                ]
            )
            print(f"⏱️  Browser launched: {time.time() - start_time:.2f}s")
            
            page = await browser.new_page()
            print(f"⏱️  Page created: {time.time() - start_time:.2f}s")
            
            try:
                # Navigate to Wise (30s timeout like API)
                print("📍 Navigating to Wise...")
                await page.goto("https://wise.com/ca/iban/calculator", timeout=30000)
                print(f"⏱️  Page loaded: {time.time() - start_time:.2f}s")
                
                await page.wait_for_load_state('networkidle')
                print(f"⏱️  Network idle: {time.time() - start_time:.2f}s")
                
                # Select country
                print("🌍 Selecting country...")
                await page.click('button:has-text("Select a Country")')
                await page.wait_for_timeout(1000)
                print(f"⏱️  Country dropdown opened: {time.time() - start_time:.2f}s")
                
                await page.click('text=United Kingdom')
                await page.wait_for_timeout(2000)
                print(f"⏱️  UK selected: {time.time() - start_time:.2f}s")
                
                # Fill form
                print("📝 Filling form...")
                await page.fill('input[name="branch_code"]', '200000')
                await page.fill('input[name="account_number"]', '55779911')
                print(f"⏱️  Form filled: {time.time() - start_time:.2f}s")
                
                # Click calculate
                print("🔢 Clicking calculate...")
                await page.click('button:has-text("Calculate IBAN")')
                await page.wait_for_timeout(3000)
                print(f"⏱️  Calculate clicked: {time.time() - start_time:.2f}s")
                
                # Get content
                print("📄 Getting content...")
                content = await page.content()
                print(f"⏱️  Content retrieved: {time.time() - start_time:.2f}s")
                print(f"📊 Content length: {len(content)}")
                
                # Look for IBAN
                print("🔍 Looking for IBAN...")
                iban_match = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', content)
                
                if iban_match:
                    iban = iban_match.group(1)
                    print(f"🎉 IBAN found: {iban}")
                    print(f"⏱️  Total time: {time.time() - start_time:.2f}s")
                else:
                    print("❌ No IBAN found")
                    
                    # Check if we're on the right page
                    title = await page.title()
                    print(f"📄 Page title: {title}")
                    
                    # Look for any IBAN pattern
                    any_iban = re.findall(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{15,32})\b', content)
                    if any_iban:
                        print(f"🔍 Found other IBANs: {any_iban[:5]}")
                    
                    # Save for inspection
                    with open('debug_api_content.html', 'w') as f:
                        f.write(content)
                    print("💾 Content saved to debug_api_content.html")
                
                await browser.close()
                print(f"⏱️  Browser closed: {time.time() - start_time:.2f}s")
                
            except Exception as e:
                print(f"❌ Error in flow: {e}")
                print(f"⏱️  Error at: {time.time() - start_time:.2f}s")
                await browser.close()
                raise e
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")

async def test_headless_vs_visual():
    """Test both headless and visual modes"""
    print("🧪 Testing headless vs visual modes...")
    
    # Test 1: Visual mode
    print("\n1. Testing VISUAL mode:")
    await debug_api_flow()
    
    # Test 2: Headless mode (like API)
    print("\n2. Testing HEADLESS mode:")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # Headless like API
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--single-process',
                    '--no-zygote'
                ]
            )
            
            page = await browser.new_page()
            
            start_time = time.time()
            
            # Quick test
            await page.goto("https://wise.com/ca/iban/calculator", timeout=30000)
            print(f"✅ Headless navigation: {time.time() - start_time:.2f}s")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Headless test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_headless_vs_visual())