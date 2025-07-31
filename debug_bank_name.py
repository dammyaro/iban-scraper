#!/usr/bin/env python3
"""
Debug script to see what bank information Wise provides
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def debug_bank_name():
    """Debug to see bank name information on Wise result page"""
    try:
        print("🔍 Debugging bank name extraction from Wise...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Navigate and fill form
            await page.goto("https://wise.com/ca/iban/calculator")
            await page.wait_for_timeout(2000)
            
            # Select UK
            await page.click('button:has-text("Select a Country")')
            await page.wait_for_timeout(1000)
            await page.click('text=United Kingdom')
            await page.wait_for_timeout(2000)
            
            # Fill form with Halifax details
            await page.fill('input[name="branch_code"]', '111702')
            await page.fill('input[name="account_number"]', '14114666')
            
            # Click calculate
            await page.click('button:has-text("Calculate IBAN")')
            await page.wait_for_timeout(3000)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Save HTML for inspection
            with open('wise_bank_result.html', 'w') as f:
                f.write(content)
            
            print("💾 Saved HTML to wise_bank_result.html")
            
            # Look for IBAN
            iban_match = re.search(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', content)
            if iban_match:
                iban = iban_match.group(1)
                print(f"✅ IBAN found: {iban}")
            
            # Look for bank name patterns
            print("\n🏦 Looking for bank name information...")
            
            # Method 1: Look for common bank name patterns
            bank_patterns = [
                r'Bank of Scotland',
                r'BANK OF SCOTLAND',
                r'Halifax',
                r'HALIFAX',
                r'Barclays',
                r'BARCLAYS',
                r'HSBC',
                r'Lloyds',
                r'NatWest',
                r'Santander',
                r'TSB',
                r'Nationwide'
            ]
            
            for pattern in bank_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"✅ Found bank pattern '{pattern}': {matches}")
            
            # Method 2: Look for text near IBAN
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if iban in line if iban_match else 'GB' in line:
                    print(f"\n📄 Context around IBAN (line {i}):")
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j}: {lines[j].strip()}")
            
            # Method 3: Look for specific elements that might contain bank info
            bank_elements = soup.find_all(['div', 'span', 'p'], string=re.compile(r'bank|Bank|BANK', re.I))
            print(f"\n🏦 Found {len(bank_elements)} elements with 'bank' text:")
            for i, elem in enumerate(bank_elements[:10]):
                text = elem.get_text().strip()
                if text and len(text) < 100:
                    print(f"  {i+1}. {text}")
            
            # Method 4: Look for elements with bank-related classes or IDs
            bank_selectors = [
                '[class*="bank"]',
                '[id*="bank"]',
                '[class*="institution"]',
                '[id*="institution"]'
            ]
            
            for selector in bank_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"\n🎯 Found elements with selector '{selector}':")
                    for elem in elements[:5]:
                        text = elem.get_text().strip()
                        if text:
                            print(f"  - {text[:100]}...")
            
            # Method 5: Look for all text that might be bank names
            all_text = soup.get_text()
            
            # Common UK bank names to search for
            uk_banks = [
                'Bank of Scotland',
                'Halifax',
                'Barclays',
                'HSBC',
                'Lloyds',
                'NatWest',
                'Santander',
                'TSB',
                'Nationwide',
                'Royal Bank of Scotland',
                'Clydesdale Bank',
                'Yorkshire Bank',
                'Metro Bank',
                'Monzo',
                'Starling Bank'
            ]
            
            print(f"\n🔍 Searching for UK bank names in page text:")
            for bank in uk_banks:
                if bank.lower() in all_text.lower():
                    print(f"✅ Found: {bank}")
            
            # Wait for manual inspection
            print(f"\n👀 Waiting 15 seconds for manual inspection...")
            await page.wait_for_timeout(15000)
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bank_name())