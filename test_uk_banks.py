#!/usr/bin/env python3
"""
UK Bank IBAN Testing - Visual browser testing for different UK bank scenarios
"""
import asyncio
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

# UK Bank Test Cases
UK_TEST_CASES = [
    {
        "name": "Barclays Bank",
        "sort_code": "200000",
        "account_number": "55779911",
        "expected_pattern": "GB.*BARC.*"
    },
    {
        "name": "HSBC Bank", 
        "sort_code": "400500",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    {
        "name": "Lloyds Bank",
        "sort_code": "309634",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    {
        "name": "NatWest Bank",
        "sort_code": "601613",
        "account_number": "31926819",
        "expected_pattern": "GB.*"
    },
    {
        "name": "Santander UK",
        "sort_code": "090128",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    {
        "name": "Halifax Bank",
        "sort_code": "110124",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    {
        "name": "TSB Bank",
        "sort_code": "772798",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    {
        "name": "Nationwide Building Society",
        "sort_code": "070116",
        "account_number": "12345678",
        "expected_pattern": "GB.*"
    },
    # Edge cases
    {
        "name": "Short Account Number",
        "sort_code": "200000",
        "account_number": "123456",
        "expected_pattern": "GB.*"
    },
    {
        "name": "Long Account Number",
        "sort_code": "200000", 
        "account_number": "123456789012",
        "expected_pattern": "GB.*"
    },
    # Invalid cases
    {
        "name": "Invalid Sort Code (too short)",
        "sort_code": "12345",
        "account_number": "12345678",
        "should_fail": True
    },
    {
        "name": "Invalid Sort Code (letters)",
        "sort_code": "ABCDEF",
        "account_number": "12345678",
        "should_fail": True
    },
    {
        "name": "Empty Account Number",
        "sort_code": "200000",
        "account_number": "",
        "should_fail": True
    }
]

async def test_uk_bank_visual(test_case, headless=False, wait_time=3):
    """Test UK bank IBAN with visual browser"""
    print(f"\n🏦 Testing: {test_case['name']}")
    print(f"   Sort Code: {test_case['sort_code']}")
    print(f"   Account Number: {test_case['account_number']}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            
            # Navigate to IBAN calculator
            print("   📍 Navigating to IBAN calculator...")
            await page.goto("https://www.iban.com/calculate-iban", timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Select UK
            print("   🇬🇧 Selecting United Kingdom...")
            await page.select_option('select[name="country"]', 'GB')
            await page.wait_for_timeout(1500)  # Wait for form to update
            
            # Fill sort code (bank code)
            print(f"   🏦 Filling sort code: {test_case['sort_code']}")
            await page.fill('input[name="bankcode"]', test_case['sort_code'])
            
            # Fill account number
            print(f"   💳 Filling account number: {test_case['account_number']}")
            await page.fill('input[name="account"]', test_case['account_number'])
            
            # Take screenshot before submission
            await page.screenshot(path=f'uk_test_before_{test_case["name"].replace(" ", "_").lower()}.png')
            
            # Submit form
            print("   📤 Submitting form...")
            await page.click('input[type="submit"]')
            
            # Wait for result
            await page.wait_for_load_state('networkidle', timeout=20000)
            
            # Wait for visual inspection
            if not headless:
                print(f"   👀 Waiting {wait_time} seconds for visual inspection...")
                await page.wait_for_timeout(wait_time * 1000)
            
            # Take screenshot after submission
            await page.screenshot(path=f'uk_test_after_{test_case["name"].replace(" ", "_").lower()}.png')
            
            # Get page content and analyze
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Save HTML for inspection
            with open(f'uk_test_{test_case["name"].replace(" ", "_").lower()}.html', 'w') as f:
                f.write(page_content)
            
            # Look for IBAN in various places
            results = {
                "iban_found": None,
                "status": None,
                "method": None,
                "all_inputs": [],
                "page_text_ibans": [],
                "errors": []
            }
            
            # Method 1: Check all input fields
            inputs = soup.find_all('input')
            for inp in inputs:
                input_name = inp.get('name', 'N/A')
                input_value = inp.get('value', 'N/A')
                input_type = inp.get('type', 'N/A')
                results["all_inputs"].append({
                    "name": input_name,
                    "value": input_value,
                    "type": input_type
                })
                
                # Look for IBAN in input fields
                if input_name == 'iban' and input_value and input_value != 'N/A':
                    value = input_value.strip()
                    if len(value) >= 15 and re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', value):
                        results["iban_found"] = value
                        results["method"] = "input_field"
                        print(f"   ✅ IBAN found in input: {value}")
            
            # Method 2: Look for IBAN patterns in page text
            gb_ibans = re.findall(r'\b(GB[0-9]{2}[A-Z]{4}[0-9]{6}[0-9]{8})\b', page_content)
            if gb_ibans:
                results["page_text_ibans"] = gb_ibans
                if not results["iban_found"]:
                    results["iban_found"] = gb_ibans[0]
                    results["method"] = "page_text"
                    print(f"   ✅ IBAN found in page text: {gb_ibans[0]}")
            
            # Method 3: Look for any IBAN pattern
            if not results["iban_found"]:
                any_ibans = re.findall(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{4,32})\b', page_content)
                if any_ibans:
                    for iban in any_ibans:
                        if iban.startswith('GB'):
                            results["iban_found"] = iban
                            results["method"] = "pattern_match"
                            print(f"   ✅ IBAN found by pattern: {iban}")
                            break
            
            # Look for error messages
            error_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'error|alert|warning', re.I))
            for elem in error_elements:
                error_text = elem.get_text().strip()
                if error_text:
                    results["errors"].append(error_text)
            
            # Check status field
            status_input = soup.find('input', {'name': 'status'})
            if status_input:
                results["status"] = status_input.get('value', '')
            
            # Print detailed results
            print(f"   📊 Results:")
            if results["iban_found"]:
                print(f"      IBAN: {results['iban_found']}")
                print(f"      Method: {results['method']}")
                print(f"      Status: {results['status']}")
                
                # Validate expected pattern
                if "expected_pattern" in test_case:
                    if re.match(test_case["expected_pattern"], results["iban_found"]):
                        print(f"      ✅ Matches expected pattern: {test_case['expected_pattern']}")
                    else:
                        print(f"      ❌ Does not match expected pattern: {test_case['expected_pattern']}")
            else:
                print(f"      ❌ No IBAN found")
                if results["errors"]:
                    print(f"      Errors: {results['errors']}")
            
            print(f"      All inputs: {len(results['all_inputs'])} found")
            
            await browser.close()
            return results
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return {"error": str(e)}

async def run_uk_bank_tests():
    """Run all UK bank tests"""
    print("🇬🇧 UK Bank IBAN Testing Suite")
    print("=" * 50)
    
    # Ask user for test mode
    print("\nTest modes:")
    print("1. Visual mode (browser visible, slower)")
    print("2. Headless mode (faster, screenshots only)")
    
    mode = input("Choose mode (1 or 2): ").strip()
    headless = mode != "1"
    wait_time = 5 if not headless else 0
    
    results = []
    
    for i, test_case in enumerate(UK_TEST_CASES, 1):
        print(f"\n{'='*20} Test {i}/{len(UK_TEST_CASES)} {'='*20}")
        
        result = await test_uk_bank_visual(test_case, headless=headless, wait_time=wait_time)
        results.append({
            "test_case": test_case,
            "result": result
        })
        
        # Brief pause between tests
        if not headless:
            await asyncio.sleep(1)
    
    # Summary
    print(f"\n\n📊 UK Bank Test Summary")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for i, test_result in enumerate(results, 1):
        test_case = test_result["test_case"]
        result = test_result["result"]
        
        print(f"\n{i}. {test_case['name']}")
        
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
            failed += 1
        elif result.get("iban_found"):
            print(f"   ✅ IBAN: {result['iban_found']}")
            successful += 1
        else:
            should_fail = test_case.get("should_fail", False)
            if should_fail:
                print(f"   ✅ Correctly failed (expected)")
                successful += 1
            else:
                print(f"   ❌ No IBAN found")
                failed += 1
    
    print(f"\nResults: {successful} successful, {failed} failed")
    print(f"Success rate: {(successful/(successful+failed)*100):.1f}%")
    
    print(f"\n📁 Files generated:")
    print(f"   - Screenshots: uk_test_*.png")
    print(f"   - HTML files: uk_test_*.html")

if __name__ == "__main__":
    asyncio.run(run_uk_bank_tests())