#!/usr/bin/env python3
"""
Debug script to inspect Wise IBAN calculator interface
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def debug_wise_interface():
    """Debug Wise IBAN calculator to find correct selectors"""
    try:
        print("🔍 Debugging Wise IBAN calculator interface...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visual mode
            page = await browser.new_page()
            
            # Navigate to Wise IBAN calculator
            print("📍 Navigating to Wise IBAN calculator...")
            await page.goto("https://wise.com/ca/iban/calculator", timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Take initial screenshot
            await page.screenshot(path='wise_initial.png')
            
            # Get page content and analyze form structure
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            print("\n📋 Looking for form elements:")
            
            # Look for input fields
            inputs = soup.find_all('input')
            print(f"Found {len(inputs)} input fields:")
            for i, inp in enumerate(inputs[:10]):  # Show first 10
                input_type = inp.get('type', 'N/A')
                input_id = inp.get('id', 'N/A')
                input_name = inp.get('name', 'N/A')
                input_testid = inp.get('data-testid', 'N/A')
                input_placeholder = inp.get('placeholder', 'N/A')
                print(f"  {i+1}. type='{input_type}', id='{input_id}', name='{input_name}', testid='{input_testid}', placeholder='{input_placeholder}'")
            
            # Look for buttons
            buttons = soup.find_all('button')
            print(f"\nFound {len(buttons)} buttons:")
            for i, btn in enumerate(buttons[:5]):  # Show first 5
                btn_text = btn.get_text().strip()
                btn_testid = btn.get('data-testid', 'N/A')
                btn_class = btn.get('class', 'N/A')
                print(f"  {i+1}. text='{btn_text}', testid='{btn_testid}', class='{btn_class}'")
            
            # Look for select elements
            selects = soup.find_all('select')
            print(f"\nFound {len(selects)} select elements:")
            for i, sel in enumerate(selects):
                sel_name = sel.get('name', 'N/A')
                sel_id = sel.get('id', 'N/A')
                sel_testid = sel.get('data-testid', 'N/A')
                print(f"  {i+1}. name='{sel_name}', id='{sel_id}', testid='{sel_testid}'")
            
            print(f"\n👀 Waiting 5 seconds for manual inspection...")
            await page.wait_for_timeout(5000)
            
            # Try to interact with the form manually
            print("\n🧪 Attempting to fill form for UK...")
            
            try:
                # Look for country input - try different selectors
                country_selectors = [
                    'input[data-testid="country-input"]',
                    'input[placeholder*="country"]',
                    'input[placeholder*="Country"]',
                    'select[name="country"]',
                    'input[name="country"]',
                    '.country-select input',
                    '[data-testid*="country"] input'
                ]
                
                country_found = False
                for selector in country_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found country input with selector: {selector}")
                            await page.click(selector)
                            await page.wait_for_timeout(500)
                            await page.fill(selector, 'GB')
                            country_found = True
                            break
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                
                if not country_found:
                    print("❌ Could not find country input")
                
                await page.wait_for_timeout(2000)
                
                # Look for bank code input
                bank_selectors = [
                    'input[data-testid="bank-code-input"]',
                    'input[placeholder*="sort"]',
                    'input[placeholder*="bank"]',
                    'input[name="bankcode"]',
                    'input[name="sortcode"]'
                ]
                
                bank_found = False
                for selector in bank_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found bank code input with selector: {selector}")
                            await page.fill(selector, '200000')
                            bank_found = True
                            break
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                
                if not bank_found:
                    print("❌ Could not find bank code input")
                
                # Look for account number input
                account_selectors = [
                    'input[data-testid="account-number-input"]',
                    'input[placeholder*="account"]',
                    'input[name="account"]',
                    'input[name="accountnumber"]'
                ]
                
                account_found = False
                for selector in account_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found account input with selector: {selector}")
                            await page.fill(selector, '55779911')
                            account_found = True
                            break
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                
                if not account_found:
                    print("❌ Could not find account input")
                
                # Look for calculate button
                button_selectors = [
                    'button[data-testid="calculate-button"]',
                    'button:has-text("Calculate")',
                    'button:has-text("Generate")',
                    'input[type="submit"]',
                    'button[type="submit"]'
                ]
                
                button_found = False
                for selector in button_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found calculate button with selector: {selector}")
                            await page.click(selector)
                            button_found = True
                            break
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                
                if not button_found:
                    print("❌ Could not find calculate button")
                
                # Wait for result
                await page.wait_for_timeout(3000)
                
                # Take screenshot after interaction
                await page.screenshot(path='wise_after_interaction.png')
                
                # Look for result
                result_content = await page.content()
                
                # Save HTML for inspection
                with open('wise_result.html', 'w') as f:
                    f.write(result_content)
                
                # Look for IBAN in result
                iban_patterns = re.findall(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', result_content)
                if iban_patterns:
                    print(f"✅ Found IBAN patterns: {iban_patterns}")
                else:
                    print("❌ No IBAN patterns found in result")
                
            except Exception as e:
                print(f"❌ Form interaction failed: {e}")
            
            print(f"\n👀 Waiting 10 seconds for final inspection...")
            await page.wait_for_timeout(10000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_wise_interface())