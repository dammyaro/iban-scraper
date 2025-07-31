#!/usr/bin/env python3
"""
Step-by-step debug of Wise interface to see what happens after country selection
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def debug_wise_step_by_step():
    """Debug each step of Wise interaction"""
    try:
        print("🔍 Step-by-step debugging of Wise interface...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Step 1: Navigate
            print("Step 1: Navigating to Wise...")
            await page.goto("https://wise.com/ca/iban/calculator")
            await page.wait_for_load_state('networkidle')
            print("✅ Page loaded")
            
            # Take initial screenshot
            await page.screenshot(path='wise_step1_initial.png')
            
            # Step 2: Find and click country dropdown
            print("\nStep 2: Looking for country dropdown...")
            
            # Try different selectors for the country button
            country_selectors = [
                'button:has-text("Select a Country")',
                'button:has-text("Select")',
                '.country-selector',
                '[data-testid*="country"]',
                'button[class*="dropdown"]'
            ]
            
            country_button = None
            for selector in country_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found country button with: {selector}")
                        country_button = element
                        break
                except:
                    continue
            
            if not country_button:
                print("❌ Could not find country dropdown button")
                # List all buttons on page
                buttons = await page.query_selector_all('button')
                print(f"Found {len(buttons)} buttons on page:")
                for i, btn in enumerate(buttons[:10]):
                    text = await btn.text_content()
                    print(f"  {i+1}. '{text.strip()}'")
                
                await browser.close()
                return
            
            # Click the country dropdown
            print("Clicking country dropdown...")
            await country_button.click()
            await page.wait_for_timeout(2000)
            
            # Take screenshot after clicking
            await page.screenshot(path='wise_step2_dropdown_open.png')
            
            # Step 3: Look for United Kingdom option
            print("\nStep 3: Looking for United Kingdom option...")
            
            uk_selectors = [
                'text=United Kingdom',
                'text=UK',
                'text=Great Britain',
                '[data-value="GB"]',
                'li:has-text("United Kingdom")',
                'option:has-text("United Kingdom")'
            ]
            
            uk_option = None
            for selector in uk_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found UK option with: {selector}")
                        uk_option = element
                        break
                except:
                    continue
            
            if not uk_option:
                print("❌ Could not find United Kingdom option")
                # List all visible text options
                content = await page.content()
                if "United Kingdom" in content:
                    print("✅ 'United Kingdom' text found in page")
                else:
                    print("❌ 'United Kingdom' text not found")
                
                # Try to find all clickable elements with text
                clickable_elements = await page.query_selector_all('a, button, li, div[role="option"]')
                print(f"Found {len(clickable_elements)} clickable elements:")
                for i, elem in enumerate(clickable_elements[:20]):
                    text = await elem.text_content()
                    if text and text.strip():
                        print(f"  {i+1}. '{text.strip()}'")
                
                await browser.close()
                return
            
            # Click United Kingdom
            print("Clicking United Kingdom...")
            await uk_option.click()
            await page.wait_for_timeout(3000)  # Wait longer for form transformation
            
            # Take screenshot after selecting UK
            await page.screenshot(path='wise_step3_uk_selected.png')
            
            # Step 4: Look for form inputs after transformation
            print("\nStep 4: Looking for form inputs after UK selection...")
            
            # Get page content to analyze
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all input fields
            inputs = soup.find_all('input')
            print(f"Found {len(inputs)} input fields:")
            for i, inp in enumerate(inputs):
                input_type = inp.get('type', 'N/A')
                input_placeholder = inp.get('placeholder', 'N/A')
                input_name = inp.get('name', 'N/A')
                input_id = inp.get('id', 'N/A')
                print(f"  {i+1}. type='{input_type}', placeholder='{input_placeholder}', name='{input_name}', id='{input_id}'")
            
            # Look for specific input patterns
            sort_code_selectors = [
                'input[placeholder*="sort"]',
                'input[placeholder*="Sort"]',
                'input[placeholder*="bank"]',
                'input[placeholder*="Bank"]',
                'input[name*="sort"]',
                'input[name*="bank"]',
                'input[type="text"]:nth-of-type(1)'
            ]
            
            account_selectors = [
                'input[placeholder*="account"]',
                'input[placeholder*="Account"]',
                'input[name*="account"]',
                'input[type="text"]:nth-of-type(2)'
            ]
            
            print("\nLooking for sort code input...")
            sort_input = None
            for selector in sort_code_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found sort code input: {selector}")
                        sort_input = element
                        break
                except:
                    continue
            
            print("\nLooking for account number input...")
            account_input = None
            for selector in account_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found account input: {selector}")
                        account_input = element
                        break
                except:
                    continue
            
            if sort_input and account_input:
                print("\n✅ Both inputs found! Filling form...")
                
                # Fill sort code
                await sort_input.fill('200000')
                print("✅ Sort code filled")
                
                # Fill account number
                await account_input.fill('55779911')
                print("✅ Account number filled")
                
                # Look for calculate button
                calc_button = await page.query_selector('button:has-text("Calculate")')
                if calc_button:
                    print("✅ Calculate button found, clicking...")
                    await calc_button.click()
                    await page.wait_for_timeout(5000)
                    
                    # Take final screenshot
                    await page.screenshot(path='wise_step4_result.png')
                    
                    # Look for result
                    final_content = await page.content()
                    import re
                    iban_match = re.search(r'\b(GB[0-9]{2}[A-Z0-9]{18})\b', final_content)
                    if iban_match:
                        print(f"🎉 IBAN found: {iban_match.group(1)}")
                    else:
                        print("❌ No IBAN found in result")
                else:
                    print("❌ Calculate button not found")
            else:
                print("❌ Could not find both input fields")
            
            # Wait for manual inspection
            print(f"\n👀 Waiting 15 seconds for manual inspection...")
            await page.wait_for_timeout(15000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_wise_step_by_step())